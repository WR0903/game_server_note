# 一、描述

Asio，即「异步 IO」（Asynchronous Input/Output），本是一个独立的c++网络程序库，似乎并不为人所知，后来因为被 Boost 相中，才声名鹊起。

什么是「异步 IO」？简单来说，就是你发起一个 IO 操作，却不用等它结束，你可以继续做其他事情，当它结束时，你会得到通知。

unix有五种io模型：

* 阻塞 I/O

* 非阻塞 I/O

* I/O 多路复用（multiplexing）（`select` 和 `poll`）

* 信号驱动 I/O（`SIGIO`）

* 异步 I/O（POSIX `aio_` 系列函数）

Asio 封装的正是「I/O 多路复用」。具体一点，`epoll` 之于 Linux，`kqueue` 之于 Mac 和 BSD。`epoll` 和 `kqueue` 比 `select` 和 `poll` 更高效。当然在 Windows 上封装的则是 IOCP（完成端口）。

Asio 的「I/O 操作」，主要还是指「网络 IO」，比如 socket 读写。

# I/O Context

每个 Asio 程序都至少有一个 `io_context` 对象，它代表了操作系统的 I/O 服务，把你的程序和这些服务链接起来。

下面这个程序空有 `io_context` 对象，却没有任何异步操作，所以它其实什么也没做，也没有任何输出。

```c++
#include <boost/asio.hpp>
#include <iostream>
#include <chrono>
int main() {
  boost::asio::io_context ioc;
  ioc.run();
  return 0;
}
```

`io_context.run` 是一个阻塞（blocking）调用，姑且把它想象成一个 loop（事件循环），直到所有异步操作完成后，loop 才结束，`run` 才返回。但是这个程序没有任何异步操作，所以 loop 直接就结束了。

# Timer

根据 I/O 操作的不同，Asio 提供了不同的 I/O 对象，比如 timer（定时器），socket，等等。 Timer 是最简单的一种 I/O 对象，可以用来实现异步调用的超时机制，下面是最简单的用法：

```c++
#include <boost/asio.hpp>
#include <iostream>
#include <chrono>
void Print(boost::system::error_code ec) {
  std::cout << "Hello, world!" << std::endl;
}
int main() {
  boost::asio::io_context ioc;
  boost::asio::steady_timer timer(ioc, std::chrono::seconds(3));
  timer.async_wait(&Print);
  ioc.run();
  return 0;
}
```

先创建一个 `steady_timer`，指定时间 3 秒，然后异步等待这个 timer，3 秒后，timer 超时结束，`Print` 被调用。

以下几点需要注意：

* 所有 I/O 对象都依赖 `io_context`，一般在构造时指定。

* `async_wait` 初始化了一个异步操作，但是这个异步操作的执行，要等到 `io_context.run` 时才开始。

* Timer 除了异步等待（`async_wait`），还可以同步等待（`wait`）。同步等待是阻塞的，直到 timer 超时结束。基本上所有 I/O 对象的操作都有同步和异步两个版本，也许是出于设计上的完整性。

* `async_wait` 的参数是一个函数对象，异步操作完成时它会被调用，所以也叫 completion handler，简称 handler，可以理解成回调函数。

* 所有 I/O 对象的 `async_xyz` 函数都有 handler 参数，对于 handler 的签名，不同的异步操作有不同的要求.

`async_wait` 的 handler 签名为 `void (boost::system::error_code)`，如果要传递额外的参数，就得用 `bind`。不妨修改一下 `Print`，让它每隔一秒打印一次计数，从 `0` 递增到 `3`。

```c++
#include <boost/asio.hpp>
#include <iostream>
#include <chrono>
void Print(boost::system::error_code ec,
           boost::asio::steady_timer* timer,
           int* count) {
  if (*count < 3) {
    std::cout << *count << std::endl;
    ++(*count);
    timer->expires_after(std::chrono::seconds(1));
    timer->async_wait(std::bind(&Print, std::placeholders::_1, timer, count));
  }
}
int main() {
  boost::asio::io_context ioc;
  boost::asio::steady_timer timer(ioc, std::chrono::seconds(1));
  int count = 0;
  timer.async_wait(std::bind(&Print, std::placeholders::_1, &timer, &count));
  ioc.run();
  return 0;
}
```

# Echo Server

Socket 也是一种 I/O 对象，相比于 timer，socket 更为常用，毕竟 Asio 是一个网络程序库。

下面以 Echo 程序为例，实现一个 TCP Server。

## 同步方式

`Session` 代表会话，负责管理一个 client 的连接。参数 `socket` 传的是值。

```c++
#include <boost/asio.hpp>
#include <array>
#include <cstdlib>
#include <iostream>
using boost::asio::ip::tcp;
constexpr std::size_t BUF_SIZE = 4096;
void Session(tcp::socket socket) {
  try {
    while (true) {
      std::array<char, BUF_SIZE> data;
      boost::system::error_code ec;
      std::size_t length = socket.read_some(boost::asio::buffer(data), ec);
      if (ec == boost::asio::error::eof) {
        std::cout << "连接被 client 妥善的关闭了" << std::endl;
        break;
      } else if (ec) {
        // 其他错误
        throw boost::system::system_error(ec);
      }
      boost::asio::write(socket, boost::asio::buffer(data, length));
    }
  } catch (const std::exception& e) {
    std::cerr << "Exception: " <<  e.what() << std::endl;
  }
}
int main(int argc, char* argv[]) {
  if (argc != 2) {
    std::cerr << "Usage: " << argv[0] << " <port>" << std::endl;
    return 1;
  }
  unsigned short port = std::atoi(argv[1]);
  boost::asio::io_context ioc;
  // 创建 Acceptor 侦听新的连接
  tcp::acceptor acceptor(ioc, tcp::endpoint(tcp::v4(), port));
  try {
    // 一次处理一个连接
    while (true) {
      Session(acceptor.accept());
    }
  } catch (const std::exception& e) {
    std::cerr << "Exception: " <<  e.what() << std::endl;
  }
  return 0;
}
```

以下几点需要注意：

* `tcp::acceptor` 也是一种 I/O 对象，用来接收 TCP 连接，连接端口由 `tcp::endpoint` 指定。

* 同步方式下，没有调用 `io_context.run`，因为 `accept`、`read_some` 和 `write` 都是阻塞的。这也意味着一次只能处理一个 Client 连接，但是可以连续 echo，除非 Client 断开连接。

* `acceptor.accept` 返回一个新的 socket 对象

## 异步方式

异步方式下，困难在于对象的生命周期，可以用 `shared_ptr` 解决。

为了同时处理多个 Client 连接，需要保留每个连接的 socket 对象，于是抽象出一个表示连接会话的类，叫 `Session`：

```c++
#include <boost/asio.hpp>
#include <array>
#include <cstdlib>
#include <iostream>
using boost::asio::ip::tcp;
constexpr std::size_t BUF_SIZE = 4096;
class Session : public std::enable_shared_from_this<Session> {
public:
  Session(tcp::socket socket) : socket_(std::move(socket)) {
  }
  void Start() {
    DoRead();
  }
  void DoRead() {
    auto self(shared_from_this());
    socket_.async_read_some(
        boost::asio::buffer(buffer_),
        [this, self](boost::system::error_code ec, std::size_t length) {
          if (!ec) {
            DoWrite(length);
          }
        });
  }
  void DoWrite(std::size_t length) {
    auto self(shared_from_this());
    boost::asio::async_write(
        socket_,
        boost::asio::buffer(buffer_, length),
        [this, self](boost::system::error_code ec, std::size_t length) {
          if (!ec) {
            DoRead();
          }
        });
  }
private:
  tcp::socket socket_;
  std::array<char, BUF_SIZE> buffer_;
};
class Server {
public:
  Server(boost::asio::io_context& ioc, std::uint16_t port)
      : acceptor_(ioc, tcp::endpoint(tcp::v4(), port)) {
    DoAccept();
  }
private:
  void DoAccept() {
    acceptor_.async_accept(
        [this](boost::system::error_code ec, tcp::socket socket) {
          if (!ec) {
            std::make_shared<Session>(std::move(socket))->Start();
          }
          DoAccept();
        });
  }
private:
  tcp::acceptor acceptor_;
};
int main(int argc, char* argv[]) {
  if (argc != 2) {
    std::cerr << "Usage: " << argv[0] << " <port>" << std::endl;
    return 1;
  }
  std::uint16_t port = std::atoi(argv[1]);
  boost::asio::io_context ioc;
  Server server(ioc, port);
  ioc.run();
  return 0;
}
```

`Session` 有两个成员变量，`socket_` 与 Client 通信，`buffer_` 是接收 Client 数据的缓存。只要 `Session` 对象在，socket 就在，连接就不断。Socket 对象是构造时传进来的，而且是通过 move 语义转移进来的。

此外，在 `Session::DoRead` 和 `Session::DoWrite` 中，因为读写都是异步的，同样为了防止当前 `Session` 不被销毁（因为超出作用域），所以要增加它的引用计数，即 `auto self(shared_from_this());` 这一句的作用。

# Echo Client

虽然用 `nc` 测试 Echo Server 非常方便，但是自己动手写一个 Echo Client 仍然十分必要。 还是先考虑同步方式。

## 同步方式

```c++
#include <boost/asio.hpp>
#include <array>
#include <cstdlib>
#include <iostream>
#include <string>
using boost::asio::ip::tcp;
constexpr std::size_t BUF_SIZE = 4096;
int main(int argc, char* argv[]) {
  if (argc != 3) {
    std::cerr << "Usage: " << argv[0] << " <host> <port>" << std::endl;
    return 1;
  }
  const char* host = argv[1];
  std::uint16_t port = static_cast<std::uint16_t>(std::atoi(argv[2]));
  try {
    boost::asio::io_context ioc;
    // 解析端点
    tcp::resolver resolver(ioc);
    auto endpoints = resolver.resolve(host, std::to_string(port));
    // 同步连接
    tcp::socket socket(ioc);
    boost::asio::connect(socket, endpoints);
    auto ep = socket.remote_endpoint();
    std::cout << "已连接到 " << ep.address().to_string() << ":" << ep.port()
              << std::endl;
    std::cout << "输入消息（输入 /quit 退出）：" << std::endl;
    std::array<char, BUF_SIZE> buf;
    while (true) {
      // 从 stdin 读取一行
      std::string line;
      std::getline(std::cin, line);
      if (line == "/quit") {
        break;
      }
      if (line.empty()) {
        continue;
      }
      // 同步发送
      boost::asio::write(socket, boost::asio::buffer(line));
      // 同步读取回显
      boost::system::error_code ec;
      std::size_t len = socket.read_some(boost::asio::buffer(buf), ec);
      if (ec == boost::asio::error::eof) {
        std::cout << "服务器关闭了连接" << std::endl;
        break;
      } else if (ec) {
        throw boost::system::system_error(ec);
      }
      std::cout << "Echo: " << std::string(buf.data(), len) << std::endl;
    }
  } catch (const std::exception& e) {
    std::cerr << "Exception: " << e.what() << std::endl;
    return 1;
  }
  return 0;
}
```

首先通过 `host` 和 `port` 解析出 endpoints，`resolve` 返回的 endpoints 类型为 `tcp::resolver::results_type`，代之以 `auto` 可以简化代码。

## 异步方式

```c++
#include <boost/asio.hpp>
#include <array>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string>
using boost::asio::ip::tcp;
constexpr std::size_t BUF_SIZE = 4096;
class Client {
public:
  Client(boost::asio::io_context& ioc,
         const std::string& host, const std::string& port)
      : socket_(ioc), resolver_(ioc) {
    // 异步解析
    resolver_.async_resolve(host, port,
        [this](boost::system::error_code ec, tcp::resolver::results_type endpoints) {
          if (ec) {
            std::cerr << "Resolve failed: " << ec.message() << std::endl;
            return;
          }
          DoConnect(endpoints);
        });
  }
private:
  void DoConnect(tcp::resolver::results_type endpoints) {
    // 异步连接，逐个端点尝试
    boost::asio::async_connect(socket_, endpoints,
        [this](boost::system::error_code ec, tcp::endpoint /*endpoint*/) {
          if (ec) {
            std::cerr << "Connect failed: " << ec.message() << std::endl;
            return;
          }
          std::cout << "已连接到服务器" << std::endl;
          DoWrite();
        });
  }
  void DoWrite() {
    // 从 stdin 读取一行（同步读取用户输入是合理的，等待用户本身是阻塞行为）
    std::string line;
    std::cout << "> " << std::flush;
    if (!std::getline(std::cin, line) || line == "/quit") {
      DoClose();
      return;
    }
    if (line.empty()) {
      DoWrite();
      return;
    }
    // 异步发送
    boost::asio::async_write(socket_, boost::asio::buffer(line),
        [this](boost::system::error_code ec, std::size_t /*length*/) {
          if (ec) {
            std::cerr << "Write failed: " << ec.message() << std::endl;
            DoClose();
            return;
          }
          DoRead();
        });
  }
  void DoRead() {
    // 异步读取回显
    socket_.async_read_some(boost::asio::buffer(buf_),
        [this](boost::system::error_code ec, std::size_t length) {
          if (ec) {
            if (ec == boost::asio::error::eof) {
              std::cout << "服务器关闭了连接" << std::endl;
            } else {
              std::cerr << "Read failed: " << ec.message() << std::endl;
            }
            DoClose();
            return;
          }
          std::cout << "Echo: " << std::string(buf_.data(), length) << std::endl;
          DoWrite(); // 继续下一轮
        });
  }
  void DoClose() {
    boost::system::error_code ec;
    socket_.close(ec);
  }
  tcp::socket socket_;
  tcp::resolver resolver_;
  std::array<char, BUF_SIZE> buf_;
};
int main(int argc, char* argv[]) {
  if (argc != 3) {
    std::cerr << "Usage: " << argv[0] << " <host> <port>" << std::endl;
    return 1;
  }
  try {
    boost::asio::io_context ioc;
    Client client(ioc, argv[1], argv[2]);
    ioc.run();
  } catch (const std::exception& e) {
    std::cerr << "Exception: " << e.what() << std::endl;
    return 1;
  }
  return 0;
}
```

就 Client 来说，异步也许并非必要，除非想同时连接多个 Server。
