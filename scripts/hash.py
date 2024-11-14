import hashlib
import zlib

#Bytes
LIMIT = 2**31
BLOCKSIZE = 2**18

def getHash(file, algo="crc32"):
    return {
        "crc32": _crc32,
        "md5": _md5,
        "sha1": _sha1,
        "sha256": _sha256
    }.get(algo, _crc32)(file)

def _crc32(fileName):
    with open(fileName, 'rb') as fh:
        hash = 0
        count = 0
        while True:
            count += BLOCKSIZE
            s = fh.read(BLOCKSIZE)
            if not s:
                break
            hash = zlib.crc32(s, hash)
            if not (count % LIMIT):
                break

        return "%08X" % (hash & 0xFFFFFFFF)

def _md5(fileName):
    hasher = hashlib.md5()
    return _hashlib_reader(fileName, hasher)

def _sha1(fileName):
    hasher = hashlib.sha1()
    return _hashlib_reader(fileName, hasher)

def _sha256(fileName):
    hasher = hashlib.sha256()
    return _hashlib_reader(fileName, hasher)

def _hashlib_reader(file, hasher):
    with open(file, 'rb') as afile:
        count = 0
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            count += BLOCKSIZE
            # print(f"{len(buf) = }", end="\r")
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
            if not count % LIMIT:
                break

    return hasher.hexdigest()
