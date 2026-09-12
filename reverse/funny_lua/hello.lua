local ffi = require("ffi")
local bit = require("bit")

local function _d(bytes, key)
  key = key or 0x80
  local t = {}
  for i = 1, #bytes do
    t[i] = string.char(bit.bxor(bytes[i], key))
  end
  return table.concat(t)
end

ffi.cdef(_d({246,239,233,228,160,170,237,237,225,240,168,246,239,233,228,160,170,225,228,228,242,172,160,245,238,243,233,231,238,229,228,160,236,239,238,231,160,236,229,238,231,244,232,172,160,233,238,244,160,240,242,239,244,172,160,233,238,244,160,230,236,225,231,243,172,160,233,238,244,160,230,228,172,160,236,239,238,231,160,239,230,230,243,229,244,169,187,138,233,238,244,160,160,160,237,245,238,237,225,240,168,246,239,233,228,160,170,225,228,228,242,172,160,245,238,243,233,231,238,229,228,160,236,239,238,231,160,236,229,238,231,244,232,169,187,138,246,239,233,228,160,170,237,225,236,236,239,227,168,245,238,243,233,231,238,229,228,160,236,239,238,231,160,243,233,250,229,169,187,138,246,239,233,228,160,160,230,242,229,229,168,246,239,233,228,160,170,240,244,242,169,187}))

local PROT_READ, PROT_WRITE, PROT_EXEC = 0x1, 0x2, 0x4
local MAP_PRIVATE, MAP_ANONYMOUS = 0x02, 0x20
local BUF_SIZE = 4096
local ROT_SHIFT = 6

local SIG_IO  = _d({236,239,238,231,160,168,170,169,168,246,239,233,228,160,170,226,245,230,172,160,245,238,243,233,231,238,229,228,160,236,239,238,231,160,227,239,245,238,244,169})
local SIG_XOR = _d({246,239,233,228,160,168,170,169,168,227,239,238,243,244,160,227,232,225,242,160,170,233,238,172,160,227,232,225,242,160,170,239,245,244,172,160,245,238,243,233,231,238,229,228,160,236,239,238,231,160,236,229,238,169})
local SIG_ROT = _d({246,239,233,228,160,168,170,169,168,227,239,238,243,244,160,227,232,225,242,160,170,233,238,172,160,227,232,225,242,160,170,239,245,244,172,160,245,238,243,233,231,238,229,228,160,236,239,238,231,160,236,229,238,172,160,233,238,244,160,243,232,233,230,244,169})

local ACCEPT = "Access granted.\n"
local DENY   = "Access denied.\n"

local READ_BLOB  = _d({211,201,238,249,211,201,238,171,205,230,184,248,247,193,184,198,247,247,189,189})
local WRITE_BLOB = _d({211,201,238,249,211,201,238,171,246,247,197,193,193,193,195,180,193,209,193,193,193,193,184,198,247,247,189,189})
local XOR_BLOB   = _d({211,201,216,211,228,195,217,248,249,209,171,178,194,176,199,202,249,197,199,196,247,194,236,194,231,229,196,175,193,193,193,193,209,212,200,193,210,201,231,199,233,227,198,201,175,184,228,201,175,184,218,201,175,184,240,177,179,205,205,189})
local ROT_BLOB   = _d({211,217,238,211,212,217,216,211,228,198,237,202,249,202,236,194,245,194,239,193,193,193,194,194,185,175,233,202,176,217,216,202,229,209,207,196,247,210,239,208,244,231,227,184,209,216,201,215,208,198,240,179,197,239,208,239,209,209,200,201,231,175,231,225,227,231,207,196,182,194,241,196,247,197,200,242,199,234,248,232,227,232,217,184,229,238,227,211,231,171,232,232,193,227,233,196,171,194,240,249,193,180,208,239,199,239,208,193,217,229,243,193,233,193,218,201,175,184,228,201,175,184,218,202,175,184,240,177,246,205,205,189})

local EXPECTED_HEX = "4205c01a0d3816d6095f6667063a14b123e0df15b522f3bc25e6b42800"

local function base64_decode(s)
  local ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
  local lookup = {}
  for i = 1, #ALPHABET do lookup[ALPHABET:sub(i, i)] = i - 1 end

  local out, acc, bits = {}, 0, 0
  for i = 1, #s do
    local c = s:sub(i, i)
    if c == "=" then break end
    local v = lookup[c]
    if v then
      acc = acc * 64 + v
      bits = bits + 6
      if bits >= 8 then
        bits = bits - 8
        out[#out + 1] = string.char(math.floor(acc / 2 ^ bits) % 256)
        acc = acc % 2 ^ bits
      end
    elseif not c:match("%s") then
      error("invalid base64 character: " .. c)
    end
  end
  return table.concat(out)
end

local function hex_decode(s)
  local out = {}
  for i = 1, #s, 2 do
    out[#out + 1] = string.char(tonumber(s:sub(i, i + 1), 16))
  end
  return table.concat(out)
end

local function load_code(blob, ctype)
  local mem = ffi.C.mmap(nil, #blob,
                         bit.bor(PROT_READ, PROT_WRITE, PROT_EXEC),
                         bit.bor(MAP_PRIVATE, MAP_ANONYMOUS), -1, 0)
  if mem == nil or ffi.cast(_d({233,238,244,240,244,242,223,244}), mem) == -1 then
    error("mmap failed")
  end
  ffi.copy(mem, blob, #blob)
  return mem, ffi.cast(ctype, mem), #blob
end

local function main()
  local expected = hex_decode(EXPECTED_HEX)

  local rmem, read_stdin,    rlen = load_code(base64_decode(READ_BLOB),  SIG_IO)
  local wmem, write_stdout,  wlen = load_code(base64_decode(WRITE_BLOB), SIG_IO)
  local xmem, xor_with_prev, xlen = load_code(base64_decode(XOR_BLOB),   SIG_XOR)
  local tmem, rot,           tlen = load_code(base64_decode(ROT_BLOB),   SIG_ROT)

  local buf = ffi.C.malloc(BUF_SIZE)
  if buf == nil then
    error("malloc failed")
  end

  local ok = false
  local n = tonumber(read_stdin(buf, BUF_SIZE))

  if n > 0 then
    local bytes = ffi.cast(_d({245,238,243,233,231,238,229,228,160,227,232,225,242,160,170}), buf)
    local len = n
    while len > 0 and (bytes[len - 1] == 10 or bytes[len - 1] == 13) do
      len = len - 1
    end

    if len > 0 then
      xor_with_prev(buf, buf, len)
      rot(buf, buf, len, ROT_SHIFT)
      local got = ffi.string(buf, len)
      ok = (#got == #expected) and (got == expected)
    end
  end

  local msg = ok and ACCEPT or DENY
  local p = ffi.cast(_d({227,239,238,243,244,160,227,232,225,242,160,170}), msg)
  write_stdout(ffi.cast(_d({246,239,233,228,160,170}), p), #msg)

  ffi.C.free(buf)
  ffi.C.munmap(tmem, tlen)
  ffi.C.munmap(xmem, xlen)
  ffi.C.munmap(wmem, wlen)
  ffi.C.munmap(rmem, rlen)

  return ok
end

os.exit(main() and 0 or 1)
