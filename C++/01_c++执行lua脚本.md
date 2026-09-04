# c++执行lua脚本

在一些项目中，我们使用c++调用lua脚本，让lua执行部分逻辑，例如一些游戏引擎，游戏的gamelogic用lua编写，引擎是c++编写，引擎让游戏逻辑跑起来就是c++调用lua脚本执行。

## 方法

### 下载下面两个第三方库，一个是lua，一个sol2.

https://github.com/ThePhD/sol2

https://github.com/lua/lua

### 构建我们的cmake工程，目录如下：

```
.
├── CMakeLists.txt
└── src
    ├── 3rdparty
    │   └── CMakeLists.txt
    ├── CMakeLists.txt
    └── main.cpp
```

将上面两个第三方库下载下来后放再3rdparty目录下面。

结果如下：

![在这里插入图片描述](https://img-blog.csdnimg.cn/6071e8c655904e229c90b7b9cce1665f.png)

### 编写最外层的CMakeLists.txt

```
PROJECT(HELLO)  # 工程名字
ADD_SUBDIRECTORY(src bin)  # 将src加到工程中，编译到bin目录下
```

### 编写3rdparty下的CMakeLists.txt

里面的两个第三方库，sol2是一个cmake工程，但lua不是，我们先新建lua.cmake，里面内容：

```
set(lua_SOURCE_DIR_ ${CMAKE_CURRENT_SOURCE_DIR}/lua-5.4.4)
add_library(lua_static STATIC
${lua_SOURCE_DIR_}/lauxlib.c
${lua_SOURCE_DIR_}/lbaselib.c
${lua_SOURCE_DIR_}/lcode.c
${lua_SOURCE_DIR_}/lcorolib.c
${lua_SOURCE_DIR_}/lctype.c
${lua_SOURCE_DIR_}/ldblib.c
${lua_SOURCE_DIR_}/ldebug.c
${lua_SOURCE_DIR_}/ldo.c
${lua_SOURCE_DIR_}/ldump.c
${lua_SOURCE_DIR_}/lfunc.c
${lua_SOURCE_DIR_}/lgc.c
${lua_SOURCE_DIR_}/linit.c
${lua_SOURCE_DIR_}/liolib.c
${lua_SOURCE_DIR_}/llex.c
${lua_SOURCE_DIR_}/lmathlib.c
${lua_SOURCE_DIR_}/lmem.c
${lua_SOURCE_DIR_}/loadlib.c
${lua_SOURCE_DIR_}/lobject.c
${lua_SOURCE_DIR_}/lopcodes.c
${lua_SOURCE_DIR_}/loslib.c
${lua_SOURCE_DIR_}/lparser.c
${lua_SOURCE_DIR_}/lstate.c
${lua_SOURCE_DIR_}/lstring.c
${lua_SOURCE_DIR_}/lstrlib.c
${lua_SOURCE_DIR_}/ltable.c
${lua_SOURCE_DIR_}/ltablib.c
#${lua_SOURCE_DIR_}/ltests.c
${lua_SOURCE_DIR_}/ltm.c
#${lua_SOURCE_DIR_}/lua.c
${lua_SOURCE_DIR_}/lundump.c
${lua_SOURCE_DIR_}/lutf8lib.c
${lua_SOURCE_DIR_}/lvm.c
${lua_SOURCE_DIR_}/lzio.c
#${lua_SOURCE_DIR_}/onelua.c
${lua_SOURCE_DIR_}/lapi.c
)
target_include_directories(lua_static PUBLIC ${lua_SOURCE_DIR_})
```

然后编写该目录下的CMakeLists.txt：

```
if(NOT TARGET sol2)
    add_subdirectory(sol2-3.3.0)
endif()
if(NOT TARGET lua)
    include(lua.cmake)
endif()
```

### 编写src下的CMakeLists.txt和main.cpp：

```
ADD_SUBDIRECTORY(3rdparty)
ADD_EXECUTABLE(hello main.cpp)
target_link_libraries(hello PUBLIC lua_static)
target_link_libraries(hello PUBLIC sol2)
```

```
#include<iostream>
#include "sol/sol.hpp"
int main(){
    sol::state m_lua_state;
    m_lua_state.open_libraries(sol::lib::base);
    std::string m_lua_script = "print (\"hello world\")";
    m_lua_state.script(m_lua_script);
    return 0;
}
```

### 按照cmake的方式编译我们的工程，运行结构如下

![在这里插入图片描述](https://img-blog.csdnimg.cn/64bb69b52abf4438a2cfee370b929337.png)

![在这里插入图片描述](https://img-blog.csdnimg.cn/85325a58df1345928402bc12ea245d1c.png)
