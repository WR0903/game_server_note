# gprof使用教程

## 描述



gprof是linux下gcc自带的c/c++调优工具，可以对程序的运行时间进行分析。



## 使用方法

### 代码

```

#include<stdio.h>

 

void new_func1(void);

 

void func1(void)

{

    printf("\n Inside func1 \n");

    int i = 0;

 

    for(;i<0xffffffff;i++);

    new_func1();

 

    return;

}

 

static void func2(void)

{

    printf("\n Inside func2 \n");

    int i = 0;

 

    for(;i<0xffffffaa;i++);

    return;

}

 

int main(void)

{

    printf("\n Inside main()\n");

    int i = 0;

 

    for(;i<0xffffff;i++);

    func1();

    func2();

 

    return 0;

}





```



```

#include<stdio.h>

 

void new_func1(void)

{

    printf("\n Inside new_func1()\n");

    int i = 0;

 

    for(;i<0xffffffee;i++);

 

    return;

}



```

上面两段代码分别保存在test_gprof.cpp test_gprof_new.cpp

### 编译并执行

```

g++  -pg test_gprof.cpp test_gprof_new.cpp -o test_gprof

```

编译完成后执行一下test_gprof，会生成一个gmon.out文件



### 分析

gprof test_gprof gmon.out