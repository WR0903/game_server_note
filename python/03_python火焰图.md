# python火焰图

python性能分析主要有几个工具:

cProfile

line\_profiler

Pyflame

Pyinstrument

Py-spy

## cProfile使用

python -m cProfile \[-s sort\_order] myscript.py

可以生成每个函数调用耗时文档

pip install flameprof

python flameprof.py input.prof > output.svg

浏览器打开可以看到火焰图

缺点：需要代码重启，对于线上服务器来说不适合做分析

## Py-spy

```plain&#x20;text
pip install py-spy
```

py-spy record -o profile.svg --pid 12345

可以直接对运行的某个进程进行分析

ctrl+c停止分析后会生成对应的火焰图
