#!/bin/bash
set -eu
cd "$(dirname "$0")"

LUAJIT_DIR=${LUAJIT_DIR:-luajit/src}
LUAJIT_LIB=${LUAJIT_LIB:-$LUAJIT_DIR/libluajit.a}
LUAJIT_BIN=${LUAJIT_BIN:-$LUAJIT_DIR/luajit}
CC=${CC:-cc}

command -v nasm    >/dev/null || { echo "nasm not found"    >&2; exit 1; }
command -v objcopy >/dev/null || { echo "objcopy not found" >&2; exit 1; }
command -v xxd     >/dev/null || { echo "xxd not found"     >&2; exit 1; }
[ -x "$LUAJIT_BIN" ] || LUAJIT_BIN=luajit
[ -f "$LUAJIT_LIB" ] || { echo "static libluajit not found: $LUAJIT_LIB" >&2; exit 1; }

build_blob() {
  asm=$1; bin=$2; b64=$3; var=$4; mode=$5

  case "$mode" in
    bin)
      echo "[build] nasm -f bin   $asm -o $bin"
      nasm -f bin "$asm" -o "$bin"
      ;;
    elf64)
      obj="${asm%.asm}.o"
      echo "[build] nasm -f elf64 $asm -o $obj"
      nasm -f elf64 "$asm" -o "$obj"
      echo "[build] objcopy --only-section=.text $obj -> $bin"
      objcopy -O binary --only-section=.text "$obj" "$bin"
      rm -f "$obj"
      ;;
    *)
      echo "build_blob: unknown mode '$mode'" >&2; exit 1
      ;;
  esac

  base64 -w 76 "$bin" > "$b64"

  obf=$("$LUAJIT_BIN" -e '
    local bit = require("bit")
    local s = io.read("*a"):gsub("%s+", "")
    local t = {}
    for i = 1, #s do t[#t+1] = tostring(bit.bxor(s:byte(i), 0x80)) end
    print("{" .. table.concat(t, ",") .. "}")
  ' < "$b64")

  awk -v obf="$obf" -v var="$var" '
    $0 ~ "^local " var " = " {
      print "local " var " = _d(" obf ")"
      next
    }
    { print }
  ' hello.lua > hello.lua.tmp
  mv hello.lua.tmp hello.lua

  echo "[build]   $bin is $(wc -c < "$bin") bytes -> $var"
}

build_blob read.asm  read.bin  read.b64  READ_BLOB  bin
build_blob write.asm write.bin write.b64 WRITE_BLOB bin
build_blob xor.asm   xor.bin   xor.b64   XOR_BLOB   elf64
build_blob rot.asm   rot.bin   rot.b64   ROT_BLOB   elf64

if [ -n "${FLAG:-}" ]; then
  echo "[build] regenerating EXPECTED_HEX via mkpass.lua"
  expected=$(luajit mkpass.lua "$FLAG")
  echo "[build]   EXPECTED_HEX = $expected"
  awk -v hex="$expected" '
    /^local EXPECTED_HEX = "/ { print "local EXPECTED_HEX = \"" hex "\""; next }
    { print }
  ' hello.lua > hello.lua.tmp
  mv hello.lua.tmp hello.lua
else
  echo "[build] FLAG not set -- keeping existing EXPECTED_HEX"
fi

echo "[build] $LUAJIT_BIN -b hello.lua hello.luac"
if [ -f "$LUAJIT_DIR/jit/bcsave.lua" ]; then
  LUA_PATH="$LUAJIT_DIR/?.lua;;" "$LUAJIT_BIN" -b hello.lua hello.luac
else
  "$LUAJIT_BIN" -b hello.lua hello.luac
fi
echo "[build]   hello.luac is $(wc -c < hello.luac) bytes of bytecode"

echo "[build] xxd -i hello.luac -> hello_luac.h"
xxd -i -n hello_bytecode hello.luac > hello_luac.h

echo "[build] $CC -O2 -no-pie -o hello wrapper.c $LUAJIT_LIB -I$LUAJIT_DIR -lm -ldl "
$CC -O2 -no-pie -s -o hello wrapper.c "$LUAJIT_LIB" -I"$LUAJIT_DIR" -lm -ldl
strip --strip-all hello

echo "[build] done: ./hello ($(wc -c < hello) bytes)"

echo "[build] cleaning intermediate files"
rm -f read.bin write.bin xor.bin rot.bin \
      read.b64 write.b64 xor.b64 rot.b64 \
      read.o   write.o   xor.o   rot.o \
      hello.luac hello_luac.h

echo "[build] kept: hello hello.lua wrapper.c build.sh mkpass.lua *.asm"
