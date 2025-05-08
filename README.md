# Astrbot_Plugins_JMPlugins
## 简介
本插件主要作用是根据提供的JMid来查询神秘作品的信息。

## 依赖
运行本插件需要安装以下包：  
[jmcomic](https://github.com/hect0x7/JMComic-Crawler-Python)  
[PicImageSearch](https://github.com/kitUIN/PicImageSearch)  
十分感谢以上作者提供的API。

## 功能
1. 根据id查询作品  
指令格式： /JM name id/包含神秘id的句子  
   比如: /JM name 114514  
        /JM name 114抽出了51个彩，其中只有4个new(句子>10个字并且当中不能有换行)

输出：若选择开启发送图片，则会返回作品的名字，作者，以及封面图。若选择关闭发送图片，则会返回作品的名字，作者。  
**请根据自己具体使用情况选择开启或者关闭发送图片的功能**

2. 根据key查询作品   
指令格式:/JM key keyword  
输出：搜索到的相关作品的名字以及id

3. Rand随机功能  
指令格式： /JM rand  
输出：随机返回一个神秘作品的名字，作者和id。  

4.搜索功能（使用的ASCii2d）  
指令格式： 回复指定图片，输入/search,即可开始搜索。  
输出：搜索到类似图片的url。  

*搜索的结果不是特别准确，请谨慎使用*

## 使用
1. 下载本插件，将本插件放入plugins文件夹下。

2. 如果是大陆地区使用，需要修改一下代理的设置：    
找到文件夹里面的option.yml，找到下面这一行选项
``` 
proxies: {
       https: 127.0.0.1:12334
      }
```
将代理设置替换为自己已经开启的代理设置。

3.安装[jmcomic](https://github.com/hect0x7/JMComic-Crawler-Python)和[PicImageSearch](https://github.com/kitUIN/PicImageSearch)两个包。

4.设置是否发送封面以及cd时间。
目前插件默认是关闭发送封面，以及cd为15秒。若需要更改，请打开main.py，找到以下两行：
```
CoolDownTime = 15
ispicture = False
```
将CoolDownTime改成自己需要的cd时间，ispicture改成True即可。

5.为开用的私聊qq号或者群聊添加权限。
指令： /JM promote/demote group/user groupid/userid  
    例如：/JM promote group 123456789   
    例如：/JM demote user 123456789  

*为了预防内鬼写的白名单:(*

## 声明
**使用本插件可能导致qq被击毙，请谨慎使用或者查询是否有内鬼再使用。**  
**使用本插件可能导致qq被击毙，请谨慎使用或者查询是否有内鬼再使用。**  
**使用本插件可能导致qq被击毙，请谨慎使用或者查询是否有内鬼再使用。**  
