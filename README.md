# 一、项目说明
本项目代码结构如下
![Alt文本](./pic.png)


# 二、安装

创建虚拟环境：
```
conda create --name myenv python=3.7
```

激活环境：
```
conda activate myenv
```
安装工具包
```
pip install -r requirements.txt
```
<br>

# 二、使用

### 3.1 使用chatgpt抽取
命令行运行
```
python chatgpt_operation.py    #操作触发型
python chatgpt_description.py  #事实型
```
运行结果日志在logs文件夹下查看

<br>

### 3.2 使用开源模型抽取

使用llama2
```
python hit_code/scripts/openai_server_demo/openai_api_server.py --base_model /path/to/base_model --gpus 0,1
python llama2_ict_operation.py
python llama2_ict_description.py
```

使用baichuan、vicuna

本地部署模型，配置对应端口以调用模型抽取
```
openai.api_base = "http://localhost:8000/v1"
```
```
python vicuna_operation.py    #操作触发型
python vicuna_description.py  #事实型
```

<br><br>

