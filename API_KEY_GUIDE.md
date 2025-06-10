# 🔑 通义千问API密钥获取指南

## 1. 访问阿里云DashScope

打开浏览器，访问：[https://dashscope.aliyun.com/](https://dashscope.aliyun.com/)

## 2. 注册/登录账号

- 如果没有阿里云账号，点击"免费注册"
- 已有账号直接登录

## 3. 进入控制台

登录后点击右上角"控制台"

## 4. 创建API Key

1. 在左侧导航栏找到"API-KEY管理"
2. 点击"创建新的API-KEY"
3. 输入名称（如：PaperBot）
4. 点击"确定"

## 5. 复制API密钥

⚠️ **重要**: API密钥只显示一次，请立即复制保存！

## 6. 配置到项目

将获取的API密钥填入项目根目录的`.env`文件：

```bash
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxx
```

## 💰 费用说明

- 通义千问提供免费额度
- qwen-turbo: 前100万tokens免费
- qwen-plus: 前100万tokens免费
- 超出免费额度后按量付费

## 🔒 安全提醒

- ❌ 不要将API密钥提交到代码仓库
- ❌ 不要在公开场合分享API密钥
- ✅ 仅在.env文件中配置
- ✅ 将.env添加到.gitignore

## 🆘 遇到问题？

1. **API密钥无效**: 确认复制完整，没有多余空格
2. **调用失败**: 检查账号是否实名认证
3. **余额不足**: 查看控制台余额和用量
4. **网络问题**: 确认网络可以访问阿里云服务

## 📞 获取帮助

- 阿里云官方文档: [https://help.aliyun.com/](https://help.aliyun.com/)
- DashScope文档: [https://dashscope.aliyun.com/docs](https://dashscope.aliyun.com/docs)