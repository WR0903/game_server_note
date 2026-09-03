---
title: centos7 配置高版本的C++
category: C++
created_at: 2026-04-26 12:31:09
view_count: 0
---

# centos7 配置高版本的C++

## 描述
centos7 默认安装的g++ 和gcc（如果没有就yum install -y gcc gcc-c++） 为4.8.5,这个支持c++11,不支持c++14,c++17以及更高的版本

## 安装步骤

### 切用户

```
su -root
```
然后执行

```
sudo yum install -y http://mirror.centos.org/centos/7/extras/x86_64/Packages/centos-release-scl-rh-2-3.el7.centos.noarch.rpm
sudo yum install -y http://mirror.centos.org/centos/7/extras/x86_64/Packages/centos-release-scl-2-3.el7.centos.noarch.rpm
```

### 安装对应版本的devtoolset

```
# gcc/g++ 10，依次类推
sudo yum install devtoolset-10-gcc-c++ 

# gcc/g++ 9
sudo yum install devtoolset-9-gcc-c++

# gcc/g++ 8
sudo yum install devtoolset-8-gcc-c++

# gcc/g++ 7
sudo yum install devtoolset-7-gcc-c++

# gcc/g++ 6
sudo yum install devtoolset-6-gcc-c++
```

选择一个自己需要的   
安装目录位于/opt/rh/devtoolset-*/目录下


### 切换gcc/g++版本

```
source /opt/rh/devtoolset-10/enable
```

如果想永久生效

```
mv /usr/bin/gcc /usr/bin/gcc-4.8.5
ln -s /opt/rh/devtoolset-10/root/bin/gcc /usr/bin/gcc

mv /usr/bin/g++ /usr/bin/g++-4.8.5
ln -s /opt/rh/devtoolset-10/root/bin/g++ /usr/bin/g++
```

### 在CMake中使用高版本的gcc/g++

```
nano /etc/profile

# 在/ect/profile增加下面两行
export CC=/opt/rh/devtoolset-10/root/bin/gcc
export CXX=/opt/rh/devtoolset-10/root/bin/g++

# 生效
source /etc/profile
```