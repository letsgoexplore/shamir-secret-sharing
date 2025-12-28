# 快速开始指南

## 5分钟快速上手

### 步骤1：准备密钥

假设您有一个32字节的hex私钥：
```
0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
```

### 步骤2：分割密钥

```bash
python3 ../src/sss_tool.py split 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
```

**输出**：
```
✓ 成功生成3个分片:
Share 1: 1:phzvXxTZYzE7O75o2gh7nbtmoLfsxvojvQEabtS10xU=
Share 2: 2:Z2Q5NoVPjE5AKptYBPC8C12Qp/tocaNqUV7OVBiX8QY=
Share 3: 3:00yAEQE9IpBpJXNITlMKefTCUTQUHJSm/muCQlyJ7/w=
```

### 步骤3：安全存储分片

**⚠️ 关键**：将3个分片存储在不同物理位置！

**推荐方案**：
- 📍 **分片1**：硬件钱包或加密USB → 家中安全位置
- 📍 **分片2**：银行保险箱 → 银行
- 📍 **分片3**：加密备份 → 办公室或可信第三方

**格式说明**：
- 每个分片格式：`x:base64_string`
- `x`是分片编号（1、2或3）
- `base64_string`是分片的base64编码

### 步骤4：恢复密钥（任意2个分片）

```bash
python3 ../src/sss_tool.py combine "1:phzvXxTZYzE7O75o2gh7nbtmoLfsxvojvQEabtS10xU=" "2:Z2Q5NoVPjE5AKptYBPC8C12Qp/tocaNqUV7OVBiX8QY="
```

**输出**：
```
✓ 恢复的秘密:
0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
```

**重要**：任意2个分片组合都可以恢复，例如：
- 分片1 + 分片2 ✓
- 分片1 + 分片3 ✓
- 分片2 + 分片3 ✓

---

## 常用场景

### 场景1：分割助记词（BIP39）

```bash
# 将助记词转换为字节后分割
MNEMONIC="word1 word2 word3 ... word12"
python3 ../src/sss_tool.py split "$MNEMONIC" --format utf8
```

### 场景2：从文件读取密钥

```bash
# 假设密钥存储在 secret.key 文件中
python3 ../src/sss_tool.py split --file secret.key --output shares.txt
```

### 场景3：保存分片到文件

```bash
# 生成分片并保存
python3 ../src/sss_tool.py split 0x... --output my_shares.txt

# 查看分片
cat my_shares.txt
```

### 场景4：恢复并保存到文件

```bash
python3 ../src/sss_tool.py combine "1:..." "2:..." --output recovered.txt
```

---

## 安全检查清单

使用前请确认：

- [ ] ✅ 已理解Shamir's Secret Sharing的基本原理
- [ ] ✅ 已阅读 [SECURITY.md](SECURITY.md) 了解威胁模型
- [ ] ✅ 已填写 [RESTORE_TEMPLATE.md](RESTORE_TEMPLATE.md) 恢复说明
- [ ] ✅ 3个分片将存储在**不同物理位置**
- [ ] ✅ 已测试恢复流程（使用2个分片成功恢复）
- [ ] ✅ 已保存恢复工具（`src/sss_tool.py`）和恢复说明文档

---

## 常见问题

**Q: 为什么需要3个分片？**  
A: 2-of-3方案允许丢失任意1个分片仍可恢复，同时保证任意1个分片不泄露信息。

**Q: 单个分片安全吗？**  
A: 是的。单个分片在信息论意义上是安全的，即使有无限计算能力也无法破解。

**Q: 能否使用云存储？**  
A: 可以，但必须加密。建议使用AES-256加密每个分片文件，密码存储在密码管理器。

**Q: 5年后还能恢复吗？**  
A: 可以。本工具仅依赖Python标准库，确保保存恢复工具和说明文档即可。

**Q: 如果丢失2个分片怎么办？**  
A: 无法恢复。这正是2-of-3方案的设计：最多只能丢失1个分片。

---

## 下一步

1. 📖 阅读 [README.md](../README.md) 了解完整功能
2. 🔒 阅读 [SECURITY.md](SECURITY.md) 了解安全细节
3. 📝 填写 [RESTORE_TEMPLATE.md](RESTORE_TEMPLATE.md) 创建恢复说明
4. 🧪 运行 `../scripts/example.sh` 进行测试

---

**记住**：密钥安全的关键在于**物理隔离**和**冗余备份**！

