# 一、安装

<span style="color: rgb(143,149,158); background-color: inherit">Libevent 是一个高性能，跨平台的 C 语言网络库。下面是在 Linux 安装 Libevent 的步骤：</span>

```shell
$ wget https://github.com/libevent/libevent/releases/download/release-2.1.8-stable/libevent-2.1.8-stable.tar.gz
$ tar -xzvf libevent-2.1.8-stable.tar.gz
$ cd libevent-2.1.8-stable
$ ./configure
$ make
$ sudo make install
```

# 二、基本概念

<span style="color: rgb(143,149,158); background-color: inherit">Libevent是基于 Reactor 模式的网络库，在 Reactor 模式中，通常都有一个事件循环(Event Loop)，在 Libevent 中，这个事件循环就是</span>`event_base`<span style="color: rgb(143,149,158); background-color: inherit">结构体：</span>

```c++
struct event_base *event_base_new(void);           // 创建事件循环
void event_base_free(struct event_base *base);     // 销毁事件循环
int event_base_dispatch(struct event_base *base);  // 运行事件循环
```

<span style="color: rgb(143,149,158); background-color: inherit">通常来说，事件循环主要有两个作用：</span>

<span style="color: rgb(143,149,158); background-color: inherit">1、用来管理事件，比如说添加我们感兴趣的事件，修改事件或删除事件。</span>

<span style="color: rgb(143,149,158); background-color: inherit">2、用来轮询它管理的所有事件，如果发现有事件活跃 (avtive)，就调用相应的回调函数去处理事件。</span>

<span style="color: rgb(143,149,158); background-color: inherit">Libevent 使用</span>`event`<span style="color: rgb(143,149,158); background-color: inherit">结构体来代表事件，可以使用</span>`event_new()`<span style="color: rgb(143,149,158); background-color: inherit">创建一个事件：</span>

```c++
struct event *event_new(struct event_base *base, // 事件循环
                        evutil_socket_t fd,      // 文件描述符
                        short what,              // 事件类型
                        event_callback_fn cb,    // 回调函数
                        void *arg);              // 传递给回调函数的参数
```

<span style="color: rgb(143,149,158); background-color: inherit">创建一个事件之后，可以使用</span>`event_add()`<span style="color: rgb(143,149,158); background-color: inherit">函数加入到事件循环</span>

```c++
int event_add(struct event *ev,             // 事件
              const struct timeval *tv);    // 超时时间
```

<span style="color: rgb(143,149,158); background-color: inherit">默认情况下，当一个事件变得活跃时，Libevent 会执行这个事件的回调函数，但同时也会将这个事件从事件循环中</span> <u><span style="color: rgb(143,149,158); background-color: inherit">移除</span></u> <span style="color: rgb(143,149,158); background-color: inherit">，例如，下面的程序，定时器只会触发一次：</span>

```c++
#include <event2/event.h>
#include <iostream>
#include <string>
void timer_cb(evutil_socket_t fd, short what, void *arg)
{
    auto str = static_cast<std::string *>(arg);
    std::cout << *str << std::endl;
}
int main()
{
    std::string str = "Hello, World!";
    auto *base = event_base_new();
    struct timeval five_seconds = {1, 0};
    auto *ev = event_new(base, -1, EV_TIMEOUT, timer_cb, (void *)&str);
    event_add(ev, &five_seconds);
    event_base_dispatch(base);
    event_free(ev);
    event_base_free(base);
    return 0;
}
```

如果想让事件不移除，<span style="color: rgb(143,149,158); background-color: inherit">创建事件时，在事件类型加上</span>`EV_PERSIST`<span style="color: rgb(143,149,158); background-color: inherit">就可以。让我们修改上面的程序，让定时器每秒就触发一次：</span>

```c++
ev = event_new(base, -1, EV_TIMEOUT|EV_PERSIST, timer_cb, (void *)&str);
```

# Tcp 服务

<span style="color: rgb(143,149,158); background-color: inherit">Libevent 使用</span>`evconnlistener`<span style="color: rgb(143,149,158); background-color: inherit">结构来表示 TCP Server，创建 TCP Server 的做法很简单：</span>

```c++
struct evconnlistener *evconnlistener_new_bind(
    struct event_base *base,        // 事件循环
    evconnlistener_cb cb,           // 回调函数，当 accept() 成功时会被调用
    void *arg,                      // 传递给回调函数的参数
    unsigned flags,                 // 选项
    int backlog,                    // tcp backlog 参数
    const struct sockaddr *sa,      // 地址
    int socklen
);
void evconnlistener_free(struct evconnlistener *lev);
```

<span style="color: rgb(143,149,158); background-color: inherit">调用</span>`evconnlistener_new_bind()`<span style="color: rgb(143,149,158); background-color: inherit">函数之后，listening socket 会自动被设置成</span> <u><span style="color: rgb(143,149,158); background-color: inherit">非阻塞</span></u> <span style="color: rgb(143,149,158); background-color: inherit">的。我们还通过</span>`flags`<span style="color: rgb(143,149,158); background-color: inherit">参数设置一些有用的选项，例如：</span>

* `LEV_OPT_CLOSE_ON_FREE`<span style="color: rgb(143,149,158); background-color: inherit">表示当调用</span>`evconnlistener_free()`<span style="color: rgb(143,149,158); background-color: inherit">时，相应的 listening socket 也会被</span>`close()`<span style="color: rgb(143,149,158); background-color: inherit">掉。</span>

* `LEV_OPT_REUSEABLE`<span style="color: rgb(143,149,158); background-color: inherit">表示会自动对 listening socket 设置</span>`SO_REUSEADDR`<span style="color: rgb(143,149,158); background-color: inherit">这个 TCP 选项。</span>

<span style="color: rgb(143,149,158); background-color: inherit">下面的程序创建了一个简单的 TCP Server:</span>

```c++
#include <event2/listener.h>
#include <arpa/inet.h>
#include <string.h>
#include <iostream>
void accept_conn_cb(struct evconnlistener *listener, evutil_socket_t fd,
                    struct sockaddr *address, int socklen, void *arg)
{
    char addr[INET_ADDRSTRLEN];
    auto *sin = reinterpret_cast<sockaddr_in *>(address);
    inet_ntop(AF_INET, &sin->sin_addr, addr, INET_ADDRSTRLEN);
    std::cout << "Accept TCP connection from: " << addr << std::endl;
}
void accept_error_cb(struct evconnlistener *listener, void *arg)
{
    auto *base = evconnlistener_get_base(listener);
    // 跨平台的错误处理
    int err = EVUTIL_SOCKET_ERROR();
    std::cerr << "Got an error on the listener: "
              << evutil_socket_error_to_string(err)
              << std::endl;
    event_base_loopexit(base, NULL);
}
int main()
{
    short port = 8000;
    struct sockaddr_in sin;
    memset(&sin, 0, sizeof(sin));
    sin.sin_family = AF_INET;
    sin.sin_addr.s_addr = htonl(INADDR_ANY);
    sin.sin_port = htons(port);
    auto *base = event_base_new();
    auto *listener = evconnlistener_new_bind(
        base, accept_conn_cb, nullptr,
        LEV_OPT_CLOSE_ON_FREE|LEV_OPT_REUSEABLE, -1,
        reinterpret_cast<struct sockaddr *>(&sin), sizeof(sin)
    );
    if (listener == nullptr) {
        std::cerr << "Couldn't create listener" << std::endl;
        return 1;
    }
    evconnlistener_set_error_cb(listener, accept_error_cb);
    event_base_dispatch(base);
    return 0;
}
```

对应的cmake

```cmake
cmake_minimum_required(VERSION 3.10)
project(libevent_study CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
# 源码安装的 libevent 通常在 /usr/local，添加搜索路径提示
set(LIBEVENT_SEARCH_PATHS /usr/local /usr)
# 查找头文件
find_path(LIBEVENT_INCLUDE_DIR
    NAMES event2/event.h
    PATH_SUFFIXES include
    PATHS ${LIBEVENT_SEARCH_PATHS}
)
# 查找库文件
find_library(LIBEVENT_LIB
    NAMES event
    PATH_SUFFIXES lib lib64
    PATHS ${LIBEVENT_SEARCH_PATHS}
)
if(NOT LIBEVENT_INCLUDE_DIR OR NOT LIBEVENT_LIB)
    message(FATAL_ERROR "libevent not found! Tried paths: ${LIBEVENT_SEARCH_PATHS}")
endif()
message(STATUS "libevent include: ${LIBEVENT_INCLUDE_DIR}")
message(STATUS "libevent library: ${LIBEVENT_LIB}")
# 自动收集当前目录下所有 C++ 源文件
file(GLOB CPP_SOURCES ${CMAKE_CURRENT_SOURCE_DIR}/*.cpp ${CMAKE_CURRENT_SOURCE_DIR}/*.cc ${CMAKE_CURRENT_SOURCE_DIR}/*.cxx)
# 为每个源文件生成独立的可执行目标
foreach(SRC_FILE ${CPP_SOURCES})
    # 获取不带扩展名的文件名作为目标名
    get_filename_component(TARGET_NAME ${SRC_FILE} NAME_WE)
    add_executable(${TARGET_NAME} ${SRC_FILE})
    target_include_directories(${TARGET_NAME} PRIVATE ${LIBEVENT_INCLUDE_DIR})
    target_link_libraries(${TARGET_NAME} ${LIBEVENT_LIB})
endforeach()
```

# 应用层buffer

非阻塞网络编程中，我们需要管理应用层缓冲区，<span style="color: rgb(143,149,158); background-color: inherit">每个 socket 都必须有一个输入缓冲区和一个输出缓冲区。</span>

* <span style="color: rgb(143,149,158); background-color: inherit">假设某个 socket 可读，并且程序已经从这个 socket 读完了数据，有 10KB 数据。但是需要 100KB 才构成一条完整的消息。那么这 10KB 数据怎么办呢？可以先把它暂时放在输入缓冲区中，等到凑齐了 100KB 再一起处理。</span>

* <span style="color: rgb(143,149,158); background-color: inherit">假设程序需要发送 100KB 的数据，但是调用</span>`write()`<span style="color: rgb(143,149,158); background-color: inherit">最多写入了 10KB，那么剩下的 90KB 数据怎么办呢？可以先 append 到输出缓冲区中，等到下次 socket 变得可写时再发送出去。</span>

<span style="color: rgb(143,149,158); background-color: inherit">Libevent 提供了</span>`bufferevent`<span style="color: rgb(143,149,158); background-color: inherit">，让缓冲区的处理变得很简单。</span>`bufferevent`<span style="color: rgb(143,149,158); background-color: inherit">的结构大概是这样的，它包含一个 socket 描述符，以及一个输入缓冲区和一个输出缓冲区：</span>

```c++
struct bufferevent {
    evutil_socket_t    fd;       // socket 描述符
    evbuffer           *input;   // 输入缓冲区
    evbuffer           *output;         // 输出缓冲区
    // ...
};
```

<span style="color: rgb(143,149,158); background-color: inherit">可以使用</span>`bufferevent_socket_new()`<span style="color: rgb(143,149,158); background-color: inherit">创建</span>`bufferevent`<span style="color: rgb(143,149,158); background-color: inherit">结构：</span>

```c++
struct bufferevent *bufferevent_socket_new(
    struct event_base *base,           // 事件循环
    evutil_socket_t fd,                // socket 描述符, 必须先设置成非阻塞的
    enum bufferevent_options options   // 选项
);
void bufferevent_free(struct bufferevent *bev);
```

<span style="color: rgb(143,149,158); background-color: inherit">其中的</span>`options`<span style="color: rgb(143,149,158); background-color: inherit">可以设置成</span>`BEV_OPT_CLOSE_ON_FREE`<span style="color: rgb(143,149,158); background-color: inherit">，也就是说当调用</span>`bufferevent_free()`<span style="color: rgb(143,149,158); background-color: inherit">，相应的 socket 描述符也会被</span>`close()`<span style="color: rgb(143,149,158); background-color: inherit">掉。</span>

`bufferevent`<span style="color: rgb(143,149,158); background-color: inherit">会自动帮我们管理应用层的缓冲区：</span>

* <span style="color: rgb(143,149,158); background-color: inherit">如果 socket 可读，</span>`bufferevent`<span style="color: rgb(143,149,158); background-color: inherit">会自动读取 socket 中的数据，并放到</span> <u><span style="color: rgb(143,149,158); background-color: inherit">输入缓冲区</span></u> <span style="color: rgb(143,149,158); background-color: inherit">中。</span>

* <span style="color: rgb(143,149,158); background-color: inherit">如果 socket 可写，</span>`bufferevent`<span style="color: rgb(143,149,158); background-color: inherit">会自动将</span> <u><span style="color: rgb(143,149,158); background-color: inherit">输出缓冲区</span></u> <span style="color: rgb(143,149,158); background-color: inherit">中的数据写到 socket 中。</span>

<span style="color: rgb(143,149,158); background-color: inherit">为了让</span>`bufferevent`<span style="color: rgb(143,149,158); background-color: inherit">自动帮我们管理缓冲区，还有一个条件，那就是要开启它的</span> <u><span style="color: rgb(143,149,158); background-color: inherit">读功能</span></u> <span style="color: rgb(143,149,158); background-color: inherit">和</span> <u><span style="color: rgb(143,149,158); background-color: inherit">写功能</span></u> <span style="color: rgb(143,149,158); background-color: inherit">：</span>

```c++
bufferevent_enable(b, EV_READ);    // 开启读功能
bufferevent_enable(b, EV_WRITE);   // 开启写功能
```

<span style="color: rgb(143,149,158); background-color: inherit">开启</span> <u><span style="color: rgb(143,149,158); background-color: inherit">读功能</span></u> <span style="color: rgb(143,149,158); background-color: inherit">之后，如果 socket 可读，</span>`bufferevent`<span style="color: rgb(143,149,158); background-color: inherit">才会自动读取 socket 中的数据到输入缓冲区中，写功能的作用也同理。默认情况下，使用</span>`bufferevent_socket_new()`<span style="color: rgb(143,149,158); background-color: inherit">创建</span>`bufferevent`<span style="color: rgb(143,149,158); background-color: inherit">之后，其实它已经自动开启了</span> <u><span style="color: rgb(143,149,158); background-color: inherit">写功能</span></u> <span style="color: rgb(143,149,158); background-color: inherit">了。</span>

<span style="color: rgb(143,149,158); background-color: inherit">一个</span>`bufferevent`<span style="color: rgb(143,149,158); background-color: inherit">可以设置三个回调函数，分别是读取回调、写入回调和事件回调。可以调用</span>`bufferevent_setcb()`<span style="color: rgb(143,149,158); background-color: inherit">设置相应的回调函数：</span>

```c++
void bufferevent_setcb(
    struct bufferevent *bufev,       // bufferevent 指针
    bufferevent_data_cb readcb,      // 读取回调
    bufferevent_data_cb writecb,     // 写入回调
    bufferevent_event_cb eventcb,    // 事件回调
    void *cbarg                      // 传递给回调函数的参数
);
```

<span style="color: rgb(143,149,158); background-color: inherit">那么这三个回调函数什么时候才会被调用呢？</span>

* <span style="color: rgb(143,149,158); background-color: inherit">当</span> <u><span style="color: rgb(143,149,158); background-color: inherit">输入缓冲区</span></u> <span style="color: rgb(143,149,158); background-color: inherit">的数据大于或等于</span> <u><span style="color: rgb(143,149,158); background-color: inherit">输入低水位</span></u> <span style="color: rgb(143,149,158); background-color: inherit">时，读取回调就会被调用。默认情况下，输入低水位的值是 0，也就是说，只要 socket 变得可读，就会调用读取回调。</span>

* <span style="color: rgb(143,149,158); background-color: inherit">当</span> <u><span style="color: rgb(143,149,158); background-color: inherit">输出缓冲区</span></u> <span style="color: rgb(143,149,158); background-color: inherit">的数据小于或等于</span> <u><span style="color: rgb(143,149,158); background-color: inherit">输出低水位</span></u> <span style="color: rgb(143,149,158); background-color: inherit">时，写入回调就会被调用。默认情况下，输出低水位的值是 0，也就是说，只有当输出缓冲区的数据都发送完了，才会调用写入回调。因此，默认情况下的写入回调也可以理解成为 write complete callback。</span>

* <span style="color: rgb(143,149,158); background-color: inherit">当连接建立、连接关闭、连接超时或者连接发生错误时，则会调用事件回调。</span>

<span style="color: rgb(143,149,158); background-color: inherit">除此之外，我们还可以设置</span>`bufferevent`<span style="color: rgb(143,149,158); background-color: inherit">的</span> <u><span style="color: rgb(143,149,158); background-color: inherit">输入高水位</span></u> <span style="color: rgb(143,149,158); background-color: inherit">，默认情况下，</span>`bufferevent`<span style="color: rgb(143,149,158); background-color: inherit">的输入缓冲区是可以无限增长的，但有时候我们想限制一个 TCP 连接的流量，这时候就可以设置一个</span> <u><span style="color: rgb(143,149,158); background-color: inherit">输入高水位</span></u> <span style="color: rgb(143,149,158); background-color: inherit">，这样就能限制输入缓冲区的大小了，保证它不会超过</span> <u><span style="color: rgb(143,149,158); background-color: inherit">输入高水位</span></u> <span style="color: rgb(143,149,158); background-color: inherit">。可以使用</span>`bufferevent_setwatermark()`<span style="color: rgb(143,149,158); background-color: inherit">设置水位线：</span>

```c++
void bufferevent_setwatermark(struct bufferevent *bufev, short events,
                              size_t lowmark, size_t highmark);
```

<span style="color: rgb(143,149,158); background-color: inherit">譬如说，我们设置某个</span>`bufferevent`<span style="color: rgb(143,149,158); background-color: inherit">的输入高水位为 128 MB：</span>

```c++
bufferevent_setwatermark(b, EV_READ, 0, 128 * 1024 * 1024);
```

<span style="color: rgb(143,149,158); background-color: inherit">最后，让我们编写一个简单的 TCP Echo Server：</span>

```c++
#include <event2/listener.h>
#include <event2/bufferevent.h>
#include <event2/buffer.h>
#include <arpa/inet.h>
#include <string.h>
#include <iostream>
void echo_read_cb(struct bufferevent *bev, void *ctx)
{
    struct evbuffer *input = bufferevent_get_input(bev);   // 输入缓存区
    struct evbuffer *output = bufferevent_get_output(bev); // 输出缓存区
    // 将输入缓冲区的数据移动到输出缓冲区
    evbuffer_add_buffer(output, input);
}
void echo_event_cb(struct bufferevent *bev, short events, void *ctx)
{
    if (events & BEV_EVENT_ERROR)
    {
        int err = EVUTIL_SOCKET_ERROR();
        std::cerr << "Got an error from bufferevent: "
                  << evutil_socket_error_to_string(err)
                  << std::endl;
    }
    if (events & (BEV_EVENT_EOF | BEV_EVENT_ERROR))
    {
        bufferevent_free(bev);
    }
}
void accept_conn_cb(struct evconnlistener *listener, evutil_socket_t fd,
                    struct sockaddr *address, int socklen, void *arg)
{
    // 设置 socket 为非阻塞
    evutil_make_socket_nonblocking(fd);
    auto *base = evconnlistener_get_base(listener);
    auto *b = bufferevent_socket_new(base, fd, BEV_OPT_CLOSE_ON_FREE);
    bufferevent_setcb(b, echo_read_cb, nullptr, echo_event_cb, nullptr);
    bufferevent_enable(b, EV_READ|EV_WRITE);
}
int main()
{
    short port = 8000;
    struct sockaddr_in sin;
    memset(&sin, 0, sizeof(sin));
    sin.sin_family = AF_INET;
    sin.sin_addr.s_addr = htonl(INADDR_ANY);
    sin.sin_port = htons(port);
    auto *base = event_base_new();
    auto *listener = evconnlistener_new_bind(
        base, accept_conn_cb, nullptr,
        LEV_OPT_CLOSE_ON_FREE|LEV_OPT_REUSEABLE, -1,
        reinterpret_cast<struct sockaddr *>(&sin), sizeof(sin));
    if (listener == nullptr)
    {
        std::cerr << "Couldn't create listener" << std::endl;
        return 1;
    }
    event_base_dispatch(base);
    return 0;
}
```
