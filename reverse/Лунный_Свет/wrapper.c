#include <stdio.h>
#include <lua.h>
#include <lauxlib.h>
#include <lualib.h>

#include "hello_luac.h"

int main(void)
{
    lua_State *L = luaL_newstate();
    if (L == NULL) {
        fputs("cannot create Lua state\n", stderr);
        return 1;
    }

    luaL_openlibs(L);

    if (luaL_loadbuffer(L, (const char *)hello_bytecode,
                        (size_t)hello_bytecode_len, "=hello") != 0) {
        fprintf(stderr, "%s\n", lua_tostring(L, -1));
        lua_close(L);
        return 1;
    }

    if (lua_pcall(L, 0, 0, 0) != 0) {
        fprintf(stderr, "%s\n", lua_tostring(L, -1));
        lua_close(L);
        return 1;
    }

    lua_close(L);
    return 0;
}
