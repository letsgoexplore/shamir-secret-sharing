# 2-of-3 Shamir's Secret Sharing 工具

一个**信息论安全**的密钥分片工具，用于安全存储高熵私钥（如32-byte hex字符串、BIP39助记词等）。

## ✨ 特性

- 🔒 **信息论安全**：任意1个分片不泄露任何关于原始密钥的信息（即使在无限计算能力下）
- ✅ **2-of-3方案**：任意2个分片可100%恢复原始密钥
- 📴 **完全离线**：所有操作在本地执行，无需网络或第三方服务
- 🔧 **简单易用**：命令行工具，支持多种输入/输出格式
- 📦 **零依赖**：仅使用Python标准库，长期可用
- 🎯 **长期维护**：适合5-10年后的密钥恢复

## 🚀 快速开始

### 安装要求

- Python 3.6 或更高版本
- 无需安装任何第三方库（仅使用标准库）

### 基本用法

#### 1. 分割密钥

```bash
# 分割hex格式的密钥
python3 src/sss_tool.py split 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef

# 输出示例：
# ✓ 成功生成3个分片:
# Share 1: 1:AbCdEf123456==
# Share 2: 2:XyZaBc789012==
# Share 3: 3:MnBvCx345678==
```

#### 2. 恢复密钥

```bash
# 使用任意2个分片恢复
python3 src/sss_tool.py combine "1:AbCdEf123456==" "2:XyZaBc789012=="

# 输出示例：
# ✓ 恢复的秘密:
# 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
```

### 高级用法

#### 从文件读取密钥

```bash
# 从文件读取（二进制）
python3 src/sss_tool.py split --file secret.key

# 从文件读取（hex格式）
echo "1234567890abcdef..." | python3 src/sss_tool.py split --format hex
```

#### 输出到文件

```bash
# 保存分片到文件
python3 src/sss_tool.py split 0x... --output shares.txt

# 恢复并保存到文件
python3 src/sss_tool.py combine "1:..." "2:..." --output recovered_secret.txt
```

#### 不同输入/输出格式

```bash
# Base64输入
python3 src/sss_tool.py split "SGVsbG8gV29ybGQ=" --format base64

# UTF-8输入（如助记词）
python3 src/sss_tool.py split "word1 word2 ... word12" --format utf8

# Base64输出
python3 src/sss_tool.py combine "1:..." "2:..." --format base64
```

## 📖 完整文档

- **[docs/SECURITY.md](docs/SECURITY.md)** - 安全文档、威胁模型、实现细节
- **[docs/RESTORE_TEMPLATE.md](docs/RESTORE_TEMPLATE.md)** - 密钥恢复说明模板
- **[docs/QUICK_START.md](docs/QUICK_START.md)** - 快速开始指南
- **[docs/DESIGN.md](docs/DESIGN.md)** - 方案设计概览

## 🔐 安全特性

### 信息论安全保证

本方案基于Shamir's Secret Sharing算法，在Galois Field GF(256)上实现：

- **任意1个分片**：无法获得关于原始密钥的任何信息（即使有无限计算能力）
- **任意2个分片**：可以100%恢复原始密钥
- **数学证明**：安全性基于信息论，不依赖于计算复杂度假设

### 与不安全方案的对比

| 方案 | 安全性 | 阈值 | 长期安全 |
|------|--------|------|----------|
| **本方案（Shamir SSS）** | ✅ 信息论安全 | ✅ 2-of-3 | ✅ 长期安全 |
| ❌ 字符串切分 | ❌ 泄露部分信息 | ❌ 需要所有分片 | ❌ 不安全 |
| ❌ XOR分片 | ❌ 可能泄露信息 | ❌ 无法实现2-of-3 | ❌ 不安全 |
| ❌ 云服务存储 | ❌ 第三方风险 | ❌ 单点故障 | ❌ 依赖服务 |

## 💾 存储建议

### ✅ 推荐做法

1. **物理隔离**：3个分片存储在不同物理位置
   - 分片1：硬件钱包/加密USB（位置A）
   - 分片2：银行保险箱（位置B）
   - 分片3：可信第三方/另一物理位置（位置C）

2. **多重备份**：为每个分片创建备份（如金属板刻录、纸质打印）

3. **加密存储（额外保护）**：每个分片文件可用AES-256加密，密码存储在密码管理器

### ❌ 避免的做法

- ❌ 存储在云服务（Notion、Telegram等）而无额外加密
- ❌ 所有分片在同一位置
- ❌ 通过未加密渠道传输分片

详细存储建议见 [docs/SECURITY.md](docs/SECURITY.md#存储安全建议)。

## 🧮 数学原理

### Shamir's Secret Sharing 概述

对于长度为`L`字节的秘密：

1. **分割**：为每个字节位置生成独立的`k-1`次多项式（在GF(256)上）
   ```
   f_i(x) = s_i + a₁x + a₂x² + ... + a_{k-1}x^{k-1}
   ```
   其中`s_i`是秘密的第`i`个字节，系数`a₁, a₂, ...`随机生成。

2. **生成分片**：计算`n`个点`(1, f(1)), (2, f(2)), (3, f(3))`

3. **恢复**：给定任意`k`个点，使用Lagrange插值计算`f(0)`，即原始秘密

### 为什么是信息论安全的？

对于`k-1`个点，存在恰好`256`个可能的`k-1`次多项式通过这些点，每个多项式对应不同的`f(0)`值，且概率相等。因此，攻击者无法获得任何信息。

详细数学证明见 [docs/SECURITY.md](docs/SECURITY.md#信息论安全证明)。

## 🔧 实现细节

- **有限域**：GF(256)，不可约多项式 `x⁸ + x⁴ + x³ + x² + 1 = 0x11D`
- **随机数生成**：使用Python `secrets`模块（密码学安全）
- **分片格式**：`x:base64(share_bytes)`
- **依赖**：仅Python标准库（`base64`, `secrets`, `argparse`）

## 📋 使用检查清单

在使用本工具前，请确认：

- [ ] 理解Shamir's Secret Sharing的基本原理
- [ ] 已阅读 [docs/SECURITY.md](docs/SECURITY.md) 安全文档
- [ ] 已填写 [docs/RESTORE_TEMPLATE.md](docs/RESTORE_TEMPLATE.md) 恢复说明
- [ ] 3个分片将存储在不同物理位置
- [ ] 已测试恢复流程（使用2个分片成功恢复）
- [ ] 已保存恢复工具（`src/sss_tool.py`）和恢复说明

## 🧪 测试示例

```bash
# 1. 生成测试密钥
SECRET="0x$(openssl rand -hex 32)"
echo "原始密钥: $SECRET"

# 2. 分割密钥
python3 src/sss_tool.py split "$SECRET" --output test_shares.txt

# 3. 恢复密钥（使用前2个分片）
SHARE1=$(grep "Share 1" test_shares.txt | cut -d' ' -f3)
SHARE2=$(grep "Share 2" test_shares.txt | cut -d' ' -f3)
python3 src/sss_tool.py combine "$SHARE1" "$SHARE2"

# 4. 验证是否匹配
# 输出应与原始密钥一致
```

## 📝 许可证

本工具为开源软件，可自由使用和修改。但**请注意**：密钥管理涉及重大安全风险，使用前请充分理解原理和风险。

## ⚠️ 免责声明

- 本工具按"现状"提供，不提供任何明示或暗示的保证
- 用户需自行承担使用本工具的所有风险
- 建议在正式使用前进行充分测试
- 对于密钥丢失或泄露，开发者不承担任何责任

## 📚 参考资料

1. **Shamir, A. (1979)**. "How to share a secret". Communications of the ACM, 22(11), 612-613.
2. **Wikipedia**: [Shamir's Secret Sharing](https://en.wikipedia.org/wiki/Shamir%27s_Secret_Sharing)
3. **RFC 3526**: More Modular Exponential (MODP) Diffie-Hellman groups

---

**版本**：1.0  
**最后更新**：2024年

如有问题或建议，请提交Issue或Pull Request。

