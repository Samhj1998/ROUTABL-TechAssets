#!/usr/bin/python3
# coding: utf-8
"""Non-destructive, explicitly owner-approved one-shot account export archive.
A unique random AES-256 disk image passphrase is stored in the current user's
macOS login Keychain using Security.framework; never on disk, argv, or stdout.
No existing app, launchd schedule, Firestore database, or backup is changed.
"""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import ctypes,os,sys,json,hashlib,secrets,subprocess,plistlib,zipfile,time,shutil

HOME=Path('/Users/yongho')
BASE=HOME/'ROUTABL-TechAssets/20_ORIGINALS/ChatGPT-Account-Exports/2026-11-05'
ORIGIN=BASE/'00_ORIGINAL'
LOCAL=BASE/'30_ENCRYPTED_LOCAL'
SSD=Path('/Volumes/SSD2TB/ROUTABL-PrivateEncrypted-Archives/ChatGPT-Export-20261105')
NAS=Path('/Volumes/Dev_Assets/ROUTABL-PrivateEncrypted-Archives/ChatGPT-Export-20261105')
AUDIT=HOME/'ROUTABL-TechAssets/60_AUDIT/120_OFFICIAL_CHATGPT_EXPORT_20261105_v01'
IMAGE_NAME='ChatGPT-Account-Export-20261105_AES256.sparseimage'
VOLNAME='ROUTABL-ChatExport-20261105'
MNT=Path('/Volumes')/VOLNAME
EXPECTED='06efc5c5c787d59b7d1bd62566974563416b29792bb17ac318335475884c5553'
SERVICE=b'com.routabl.techassets.chatgpt-export-20261105.aes256'
ACCOUNT=b'yongho'
SEC=ctypes.CDLL('/System/Library/Frameworks/Security.framework/Security')
C=ctypes
SEC.SecKeychainFindGenericPassword.argtypes=[C.c_void_p,C.c_uint32,C.c_char_p,C.c_uint32,C.c_char_p,C.POINTER(C.c_uint32),C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)]
SEC.SecKeychainFindGenericPassword.restype=C.c_int32
SEC.SecKeychainAddGenericPassword.argtypes=[C.c_void_p,C.c_uint32,C.c_char_p,C.c_uint32,C.c_char_p,C.c_uint32,C.c_void_p,C.POINTER(C.c_void_p)]
SEC.SecKeychainAddGenericPassword.restype=C.c_int32
SEC.SecKeychainItemFreeContent.argtypes=[C.c_void_p,C.c_void_p]
SEC.SecKeychainItemFreeContent.restype=C.c_int32
os.umask(0o077)

def status(event, **kw):
    print(json.dumps(dict(step=event,at_kst=datetime.now(ZoneInfo('Asia/Seoul')).isoformat(timespec='seconds'),**kw),ensure_ascii=False),flush=True)

def fingerprint(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while True:
            b=f.read(8*1024*1024)
            if not b:break
            h.update(b)
    return h.hexdigest()

def keychain_find():
    length=C.c_uint32();buffer=C.c_void_p()
    rc=SEC.SecKeychainFindGenericPassword(None,len(SERVICE),SERVICE,len(ACCOUNT),ACCOUNT,C.byref(length),C.byref(buffer),None)
    if rc == -25300:return None
    if rc != 0:raise RuntimeError('KEYCHAIN_FIND_DENIED_STATUS_'+str(rc))
    try:return C.string_at(buffer,length.value)
    finally:SEC.SecKeychainItemFreeContent(None,buffer)

def keychain_get_or_create():
    found=keychain_find()
    if found:
        assert len(found)>=40,'KEYCHAIN_EXISTING_WEAK'
        status('KEYCHAIN_RECOVERY_ITEM_ALREADY_PRESENT')
        return found
    secret=secrets.token_urlsafe(72).encode('ascii')
    buff=C.create_string_buffer(secret)
    rc=SEC.SecKeychainAddGenericPassword(None,len(SERVICE),SERVICE,len(ACCOUNT),ACCOUNT,len(secret),C.cast(buff,C.c_void_p),None)
    if rc!=0:raise RuntimeError('KEYCHAIN_CREATE_DENIED_STATUS_'+str(rc))
    chk=keychain_find()
    assert chk==secret,'KEYCHAIN_PERSISTENCE_MISMATCH'
    status('KEYCHAIN_ITEM_CREATED_AND_RETRIEVED_NO_SECRET_EXPOSED')
    return chk

def run_hdi(args,password,deadline):
    proc=subprocess.run(['/usr/bin/hdiutil']+args,input=password+b'\n',stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=deadline)
    if proc.returncode!=0:
        raise RuntimeError('HDIUTIL_FAILED_'+args[0]+'_EXIT_'+str(proc.returncode))
    return proc.stdout

def mount_image(image,password,readonly=True):
    assert not MNT.exists() and not os.path.ismount(MNT), 'MOUNT_POINT_OCCUPIED'
    opts=['attach','-quiet','-nobrowse','-noautoopen']
    if readonly:opts.append('-readonly')
    opts+=['-stdinpass','-mountpoint',str(MNT),str(image)]
    run_hdi(opts,password,180)
    assert os.path.ismount(MNT),'MOUNT_NOT_ACTIVE'

def detach_image():
    for _ in range(3):
        if not os.path.ismount(MNT):return True
        p=subprocess.run(['/usr/bin/hdiutil','detach','-quiet',str(MNT)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90)
        if p.returncode==0 and not os.path.ismount(MNT):return True
        time.sleep(2)
    return not os.path.ismount(MNT)

def image_encrypted(path,password):
    p=subprocess.run(['/usr/bin/hdiutil','imageinfo','-plist','-stdinpass',str(path)],input=password+b'\n',capture_output=True,timeout=70)
    assert p.returncode==0,'IMAGEINFO_NOT_AVAILABLE'
    d=plistlib.loads(p.stdout)
    assert d.get('Properties',{}).get('Encrypted') is True,'IMAGE_NOT_ENCRYPTED'
    return True

def secure_directory(path):
    if path.is_symlink():raise RuntimeError('SYMLINK_DESTINATION_FORBIDDEN')
    if not path.exists():path.mkdir(mode=0o700,parents=True)
    assert path.is_dir() and not path.is_symlink()
    # SMB servers may not support local POSIX chmod; do not change server ACLs.
    if not str(path).startswith('/Volumes/Dev_Assets/'):
        os.chmod(path,0o700)

def copy_atomic(src,dest):
    assert src.is_file()
    if dest.exists():
        assert dest.stat().st_size==src.stat().st_size and fingerprint(dest)==fingerprint(src),'DESTINATION_HASH_CONFLICT'
        status('CIPHERTEXT_ALREADY_MATCHES',storage=str(dest.parent))
        return
    tmp=dest.with_name('.'+dest.name+'.incomplete')
    assert not tmp.exists(),'STAGED_DESTINATION_ALREADY_EXISTS'
    h=hashlib.sha256()
    with src.open('rb') as r, tmp.open('xb') as w:
        while True:
            b=r.read(8*1024*1024)
            if not b:break
            w.write(b)
            h.update(b)
        w.flush();os.fsync(w.fileno())
    assert tmp.stat().st_size==src.stat().st_size,'COPY_LENGTH_MISMATCH'
    assert fingerprint(tmp)==h.hexdigest(),'COPY_HASH_MISMATCH'
    os.chmod(tmp,0o600)
    os.replace(tmp,dest)
    assert dest.stat().st_size==src.stat().st_size
    status('CIPHERTEXT_COPY_WRITTEN_SHA_VERIFIED',storage=str(dest.parent),bytes=dest.stat().st_size)

def verify_restored_contents(image, password, source_name):
    before=False
    try:
        mount_image(image,password,readonly=True)
        before=True
        p=MNT/source_name
        assert p.is_file(),'RECOVERED_ZIP_NOT_FOUND'
        assert p.stat().st_size==1589174843,'RECOVERED_SIZE_MISMATCH'
        assert fingerprint(p)==EXPECTED,'RECOVERED_ZIP_SHA_MISMATCH'
        with zipfile.ZipFile(p) as z:
            assert z.testzip() is None,'RECOVERED_ZIP_CRC_FAIL'
        status('READONLY_RESTORE_VERIFIED',image_storage=str(Path(image).parent),bytes=p.stat().st_size,sha256=EXPECTED,zip_crc='PASS')
    finally:
        if before or os.path.ismount(MNT):
            assert detach_image(),'FAILED_TO_DETACH_RECOVERY_IMAGE'
    assert not os.path.ismount(MNT),'IMAGE_LEFT_MOUNTED'

def main():
    assert os.geteuid()==501 and os.getuid()==501, 'UNEXPECTED_USER'
    assert os.path.ismount('/Volumes/SSD2TB') and os.path.ismount('/Volumes/Dev_Assets'),'STORAGE_NOT_MOUNTED'
    assert not MNT.exists(),'PREEXISTING_MOUNT_PATH'
    original=list(ORIGIN.glob('*.zip'))
    assert len(original)==1
    src=original[0]
    assert src.stat().st_size==1589174843 and fingerprint(src)==EXPECTED,'OFFICIAL_EXPORT_SOURCE_HASH_MISMATCH'
    for d in (LOCAL,SSD,NAS):
        secure_directory(d)
    stage=LOCAL/IMAGE_NAME
    secret=keychain_get_or_create()
    if stage.exists():
        assert stage.is_file() and image_encrypted(stage,secret)
        status('RESUME_PREVIOUSLY_CREATED_ENCRYPTED_IMAGE')
    else:
        status('CREATING_NEW_AES256_APFS_DISK_IMAGE',virtual_capacity='3GiB')
        run_hdi(['create','-quiet','-size','3g','-fs','APFS','-volname',VOLNAME,'-type','SPARSE','-encryption','AES-256','-stdinpass',str(stage)],secret,180)
        assert stage.is_file() and image_encrypted(stage,secret)
        status('AES256_DISK_IMAGE_CREATED_ENCRYPTION_VERIFIED')
    mounted=False
    try:
        mount_image(stage,secret,readonly=False)
        mounted=True
        target=MNT/src.name
        assert not target.exists()
        h=hashlib.sha256()
        with src.open('rb') as r,target.open('xb') as w:
            while True:
                b=r.read(8*1024*1024)
                if not b:break
                h.update(b);w.write(b)
            w.flush();os.fsync(w.fileno())
        assert h.hexdigest()==EXPECTED and fingerprint(target)==EXPECTED,'ZIP_WRITE_SHA_MISMATCH'
        with zipfile.ZipFile(target) as z:assert z.testzip() is None
        status('ZIP_WRITTEN_INSIDE_ENCRYPTED_VOLUME_CRC_AND_SHA_PASS',zip_bytes=target.stat().st_size)
    finally:
        if mounted or os.path.ismount(MNT):
            assert detach_image(),'ENCRYPTED_VOLUME_FAILED_TO_LOCK'
    assert not os.path.ismount(MNT),'LOCAL_VOLUME_LEFT_OPEN'
    assert image_encrypted(stage,secret)
    local_cipher_sha=fingerprint(stage)
    local_cipher_bytes=stage.stat().st_size
    status('ENCRYPTED_LOCAL_FILE_SEALED',cipher_bytes=local_cipher_bytes,cipher_sha256=local_cipher_sha)
    for label,folder in [('SSD',SSD),('NAS',NAS)]:
        target=folder/IMAGE_NAME
        copy_atomic(stage,target)
        assert fingerprint(target)==local_cipher_sha and target.stat().st_size==local_cipher_bytes
        assert image_encrypted(target,secret)
        status('CIPHER_SHA_MATCH_AND_ENCRYPTED',storage=label)
    # Independent read-only recovery of each stored ciphertext copy, not source staging.
    verify_restored_contents(SSD/IMAGE_NAME,secret,src.name)
    # For NAS, independently read ciphertext from SMB back into the FileVault disk,
    # then mount this *restored* copy read-only for full archive data validation.
    nas_recovered=LOCAL/('NAS_INDEPENDENT_RECOVERY_'+IMAGE_NAME)
    copy_atomic(NAS/IMAGE_NAME,nas_recovered)
    assert fingerprint(nas_recovered)==local_cipher_sha
    verify_restored_contents(nas_recovered,secret,src.name)
    # Preserve encrypted NAS recovery copy only if required as extra immutable original?
    # It is redundant. Do not delete it automatically to keep full evidence and safety.
    receipt={
      'receipt_version':'0.1','result':'SUCCESS_TWO_INDEPENDENT_READONLY_RESTORES',
      'created_kst':datetime.now(ZoneInfo('Asia/Seoul')).isoformat(timespec='seconds'),
      'source_archive_path':str(src),'source_archive_bytes':src.stat().st_size,
      'source_archive_sha256':EXPECTED,
      'algorithm':'AES-256_MACOS_ENCRYPTED_APFS_SPARSEIMAGE',
      'ciphertext_path_local':str(stage),'ciphertext_path_ssd':str(SSD/IMAGE_NAME),
      'ciphertext_path_nas':str(NAS/IMAGE_NAME),'nas_restore_readonly_copy':str(nas_recovered),
      'ciphertext_bytes':local_cipher_bytes,'ciphertext_sha256':local_cipher_sha,
      'ssd_copy_sha256_verified':True,'nas_copy_sha256_verified':True,
      'ssd_readonly_restore_zip_sha256_verified':True,'nas_independent_readonly_restore_zip_sha256_verified':True,
      'zip_crc_pass_on_original_and_both_restore_mounts':True,
      'password_storage':'MACOS_LOGIN_KEYCHAIN_LOCAL_ONLY_NO_SECRET_IN_RECEIPT',
      'disaster_recovery_if_mac_keychain_unavailable':'KEY_ESCROW_PENDING',
      'any_plaintext_on_unencrypted_ssd_or_nas':False,
      'encrypted_volumes_detached':not os.path.ismount(MNT),
      'google_drive_upload':False,'nas_pruning':False,'existing_backup_jobs_untouched':True,
      'original_archive_and_downloads_untouched':True
    }
    name=AUDIT/'AES256_FULL_EXPORT_BACKUP_AND_RESTORE_20261105_v0.1.json'
    assert not name.exists()
    data=(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode('utf8')
    with name.open('xb') as f:
        f.write(data);f.flush();os.fsync(f.fileno())
    os.chmod(name,0o600)
    status('FINAL_SUCCESS_RECEIPT_CREATED',receipt_path=str(name),receipt_sha256=hashlib.sha256(data).hexdigest())
if __name__=='__main__':
    try:main()
    except Exception as e:
        status('FAILED_SAFE',reason_type=type(e).__name__,short=str(e)[:150],no_backup_success_claim=True,mounted=os.path.ismount(MNT))
        sys.exit(3)
