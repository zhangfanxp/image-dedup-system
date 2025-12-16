拉取项目镜像

git clone https://github.com/zhangfanxp/image-dedup-system.git

1、创建uv虚拟环境并激活

uv venv --python 3.12 && source .venv/bin/activate

2、安装项目依赖

uv pip install -r requirements.txt

3、创建数据库

mysql -u root -p < setup.sql

4、把模型文件resnet50-11ad3fa6.pth拷贝至系统文件夹

.cache/torch/hub/checkpoints/

5、运行命令

streamlit run app/main.py


----------------------------------------------------------------

app/db文件夹下的session.py中,要把mysql的root密码改为你本地设置的密码.