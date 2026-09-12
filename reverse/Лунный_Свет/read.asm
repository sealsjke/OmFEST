; read.asm -- x86-64 Linux read(2) from stdin, as a raw position-independent blob.
;
;   long read_stdin(void *buf, unsigned long count);
;       rdi = buf, rsi = count
;
; Issues exactly one read(0, buf, count) and returns what the kernel returned:
; the byte count, 0 at EOF, or -errno. It does not write anything, and it has
; no idea what the caller plans to do with the bytes.
;
; Assembled with `nasm -f bin`: no ELF header, no libc, no relocations, and
; no absolute addresses, so it can be dropped at any address and called.

BITS 64
default rel

    mov     rdx, rsi        ; rdx = count            (read's 3rd argument)
    mov     rsi, rdi        ; rsi = buf              (read's 2nd argument)
    xor     edi, edi        ; rdi = 0 = stdin        (read's 1st argument)
    xor     eax, eax        ; rax = 0                (SYS_read)
    syscall                 ; rax = bytes read, or -errno
    ret
