section .text
global rot

rot:
    mov r10, rdx              ; save len (rdx will be clobbered by idiv)
    test r10, r10
    jz .done

    ; shift %= 26, with Python-style non-negative modulo
    mov eax, ecx
    cdq
    mov r8d, 26
    idiv r8d
    mov ecx, edx              ; remainder
    test ecx, ecx
    jns .shift_ok
    add ecx, 26
.shift_ok:

.loop:
    movzx eax, byte [rdi]     ; b = *in

    cmp al, 'A'
    jb .check_lower
    cmp al, 'Z'
    ja .check_lower

    ; uppercase
    sub eax, 'A'
    add eax, ecx
    cmp eax, 26
    jb .upper_ok
    sub eax, 26
.upper_ok:
    add eax, 'A'
    jmp .store

.check_lower:
    cmp al, 'a'
    jb .store_orig
    cmp al, 'z'
    ja .store_orig

    ; lowercase
    sub eax, 'a'
    add eax, ecx
    cmp eax, 26
    jb .lower_ok
    sub eax, 26
.lower_ok:
    add eax, 'a'
    jmp .store

.store_orig:
.store:
    mov [rsi], al

    inc rdi
    inc rsi
    dec r10
    jnz .loop

.done:
    ret

section .note.GNU-stack noalloc noexec nowrite progbits
