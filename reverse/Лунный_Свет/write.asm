; write.asm -- x86-64 Linux write(2) to stdout, as a raw position-independent blob.
;
;   long write_stdout(void *buf, unsigned long count);
;       rdi = buf, rsi = count
;
; Issues exactly one write(1, buf, count) and returns what the kernel returned:
; the byte count or -errno. It writes precisely `count` bytes -- no NUL scan,
; no strlen -- so the caller decides how much to send, and binary payloads
; containing NUL bytes survive intact.
;
; Assembled with `nasm -f bin`: no ELF header, no libc, no relocations, and
; no absolute addresses, so it can be dropped at any address and called.

BITS 64
default rel

    mov     rdx, rsi        ; rdx = count            (write's 3rd argument)
    mov     rsi, rdi        ; rsi = buf              (write's 2nd argument)
    mov     edi, 1          ; rdi = 1 = stdout       (write's 1st argument)
    mov     eax, 1          ; rax = 1                (SYS_write)
    syscall                 ; rax = bytes written, or -errno
    ret
