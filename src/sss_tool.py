#!/usr/bin/env python3
"""
2-of-3 Shamir's Secret Sharing Tool
信息论安全的密钥分片工具

使用方法:
    python sss_tool.py split <secret>          # 分割密钥
    python sss_tool.py combine <share1> <share2>  # 恢复密钥

安全特性:
    - 信息论安全：任意1份分片不泄露任何信息
    - 2-of-3方案：任意2份可完全恢复
    - 完全离线操作
"""

import sys
import argparse
import base64
import secrets
from typing import List, Tuple


class GF256:
    """Galois Field GF(2^8) 用于Shamir's Secret Sharing"""
    
    # 不可约多项式: x^8 + x^4 + x^3 + x^2 + 1 = 0x11D
    GF_MOD = 0x11D
    
    @staticmethod
    def add(a: int, b: int) -> int:
        """GF(256)加法 = XOR"""
        return a ^ b
    
    @staticmethod
    def multiply(a: int, b: int) -> int:
        """GF(256)乘法（使用对数表加速）"""
        if a == 0 or b == 0:
            return 0
        
        # 使用预计算的对数表和反对数表
        log_a = GF256._log_table[a]
        log_b = GF256._log_table[b]
        log_sum = (log_a + log_b) % 255
        return GF256._exp_table[log_sum]
    
    @staticmethod
    def divide(a: int, b: int) -> int:
        """GF(256)除法 = a * b^(-1)"""
        if b == 0:
            raise ValueError("Division by zero in GF(256)")
        if a == 0:
            return 0
        log_a = GF256._log_table[a]
        log_b = GF256._log_table[b]
        log_diff = (log_a - log_b) % 255
        return GF256._exp_table[log_diff]
    
    @staticmethod
    def _init_tables():
        """初始化对数和反对数表"""
        exp_table = [0] * 256
        log_table = [0] * 256
        
        g = 1
        for i in range(255):
            exp_table[i] = g
            log_table[g] = i
            g = (g << 1) ^ (0x11D if g & 0x80 else 0)
        
        exp_table[255] = exp_table[0]
        return exp_table, log_table
    
    _exp_table, _log_table = _init_tables()


def evaluate_polynomial(coefficients: List[int], x: int) -> int:
    """
    在GF(256)上计算多项式 f(x) = c0 + c1*x + c2*x^2 + ...
    
    Args:
        coefficients: 多项式系数 [c0, c1, c2, ...]
        x: 评估点
    
    Returns:
        f(x)的值
    """
    result = 0
    power = 1
    for coeff in coefficients:
        result = GF256.add(result, GF256.multiply(coeff, power))
        power = GF256.multiply(power, x)
    return result


def lagrange_interpolation(share_x: List[int], share_y: List[int], x: int = 0) -> int:
    """
    Lagrange插值恢复秘密（在GF(256)上）
    
    Args:
        share_x: 分片的x坐标 [x1, x2, ...]
        share_y: 分片的y坐标 [y1, y2, ...]
        x: 要计算的点（恢复秘密时x=0）
    
    Returns:
        f(x)的值（x=0时返回秘密）
    """
    if len(share_x) != len(share_y):
        raise ValueError("share_x and share_y must have same length")
    if len(share_x) < 2:
        raise ValueError("Need at least 2 shares to recover secret")
    
    result = 0
    for i in range(len(share_x)):
        numerator = 1
        denominator = 1
        for j in range(len(share_x)):
            if i != j:
                # 计算 (x - xj)
                numerator = GF256.multiply(numerator, GF256.add(x, share_x[j]))
                # 计算 (xi - xj)
                denominator = GF256.multiply(denominator, GF256.add(share_x[i], share_x[j]))
        
        # 计算 (x - xj) / (xi - xj)
        lagrange_basis = GF256.divide(numerator, denominator)
        # 累加 yi * lagrange_basis
        result = GF256.add(result, GF256.multiply(share_y[i], lagrange_basis))
    
    return result


def split_secret(secret_bytes: bytes, n: int = 3, k: int = 2) -> List[Tuple[int, bytes]]:
    """
    使用Shamir's Secret Sharing分割秘密
    
    Args:
        secret_bytes: 要分割的秘密（字节）
        n: 总分片数
        k: 恢复所需的最小分片数
    
    Returns:
        [(x1, share1), (x2, share2), ...] 每个share是bytes
    """
    if len(secret_bytes) == 0:
        raise ValueError("Secret cannot be empty")
    if k > n:
        raise ValueError("k cannot be greater than n")
    if k < 2:
        raise ValueError("k must be at least 2")
    if n > 255:
        raise ValueError("n cannot exceed 255 (GF(256)限制)")
    
    secret_length = len(secret_bytes)
    shares = []
    
    # 为每个字节位置生成独立的多项式
    for byte_pos in range(secret_length):
        # 构造k-1次多项式: f(x) = secret + a1*x + a2*x^2 + ... + a(k-1)*x^(k-1)
        coefficients = [secret_bytes[byte_pos]]  # c0 = secret byte
        for _ in range(k - 1):
            coefficients.append(secrets.randbelow(256))  # 随机系数
        
        # 为每个分片计算 f(x) 在x=1,2,3,...的值
        for share_idx in range(n):
            x = share_idx + 1  # x坐标: 1, 2, 3, ... (避免0，因为f(0)=secret)
            y = evaluate_polynomial(coefficients, x)
            
            if byte_pos == 0:
                shares.append((x, bytes([y])))
            else:
                shares[share_idx] = (shares[share_idx][0], shares[share_idx][1] + bytes([y]))
    
    return shares


def combine_shares(shares: List[Tuple[int, bytes]]) -> bytes:
    """
    从分片中恢复秘密
    
    Args:
        shares: [(x1, share1), (x2, share2), ...]
    
    Returns:
        恢复的秘密（字节）
    """
    if len(shares) < 2:
        raise ValueError("Need at least 2 shares to recover secret")
    
    # 验证所有share长度相同
    share_length = len(shares[0][1])
    for x, share in shares:
        if len(share) != share_length:
            raise ValueError(f"All shares must have same length. Found {share_length} and {len(share)}")
    
    # 逐个字节恢复
    recovered_bytes = []
    for byte_pos in range(share_length):
        share_x = [share[0] for share in shares]
        share_y = [share[1][byte_pos] for share in shares]
        
        # 使用Lagrange插值在x=0处计算（即秘密值）
        secret_byte = lagrange_interpolation(share_x, share_y, x=0)
        recovered_bytes.append(secret_byte)
    
    return bytes(recovered_bytes)


def encode_share(x: int, share_bytes: bytes) -> str:
    """
    编码分片为可打印字符串格式: "x:base64(share)"
    
    Args:
        x: x坐标
        share_bytes: 分片字节
    
    Returns:
        编码后的字符串
    """
    share_b64 = base64.b64encode(share_bytes).decode('ascii')
    return f"{x}:{share_b64}"


def decode_share(encoded: str) -> Tuple[int, bytes]:
    """
    解码分片字符串
    
    Args:
        encoded: "x:base64(share)" 格式的字符串
    
    Returns:
        (x坐标, 分片字节)
    """
    try:
        parts = encoded.split(':', 1)
        if len(parts) != 2:
            raise ValueError("Invalid share format")
        x = int(parts[0])
        share_bytes = base64.b64decode(parts[1])
        return (x, share_bytes)
    except Exception as e:
        raise ValueError(f"Failed to decode share: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="2-of-3 Shamir's Secret Sharing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 分割密钥（输入hex字符串）
  python sss_tool.py split 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
  
  # 恢复密钥（从2个分片）
  python sss_tool.py combine "1:AbCdEf==" "2:XyZaBc=="
  
  # 从文件读取密钥
  python sss_tool.py split --file secret.key
  
  # 输出到文件
  python sss_tool.py split 0x... --output shares.txt
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # split 命令
    split_parser = subparsers.add_parser('split', help='分割秘密')
    split_parser.add_argument('secret', nargs='?', help='要分割的秘密（hex/hex格式，如 0x... 或直接hex字符串）')
    split_parser.add_argument('--file', '-f', help='从文件读取秘密')
    split_parser.add_argument('--output', '-o', help='输出分片到文件（每行一个分片）')
    split_parser.add_argument('--format', choices=['hex', 'base64', 'utf8'], default='hex',
                              help='输入格式（默认: hex）')
    
    # combine 命令
    combine_parser = subparsers.add_parser('combine', help='恢复秘密')
    combine_parser.add_argument('shares', nargs='+', help='至少2个分片（格式: x:base64）')
    combine_parser.add_argument('--format', choices=['hex', 'base64', 'utf8'], default='hex',
                                help='输出格式（默认: hex）')
    combine_parser.add_argument('--output', '-o', help='输出恢复的秘密到文件')
    
    args = parser.parse_args()
    
    if args.command == 'split':
        # 读取秘密
        if args.file:
            with open(args.file, 'rb') as f:
                secret_bytes = f.read()
        elif args.secret:
            secret_str = args.secret.strip()
            # 支持 0x... 或直接hex字符串
            if secret_str.startswith('0x') or secret_str.startswith('0X'):
                secret_str = secret_str[2:]
            
            if args.format == 'hex':
                try:
                    secret_bytes = bytes.fromhex(secret_str)
                except ValueError as e:
                    print(f"错误: 无效的hex字符串: {e}", file=sys.stderr)
                    sys.exit(1)
            elif args.format == 'base64':
                try:
                    secret_bytes = base64.b64decode(secret_str)
                except Exception as e:
                    print(f"错误: 无效的base64字符串: {e}", file=sys.stderr)
                    sys.exit(1)
            elif args.format == 'utf8':
                secret_bytes = secret_str.encode('utf-8')
        else:
            print("错误: 必须提供秘密（通过参数或--file）", file=sys.stderr)
            sys.exit(1)
        
        if len(secret_bytes) == 0:
            print("错误: 秘密不能为空", file=sys.stderr)
            sys.exit(1)
        
        # 分割秘密
        try:
            shares = split_secret(secret_bytes, n=3, k=2)
            
            # 编码分片
            encoded_shares = [encode_share(x, share) for x, share in shares]
            
            # 输出
            if args.output:
                with open(args.output, 'w') as f:
                    for i, share in enumerate(encoded_shares, 1):
                        f.write(f"Share {i}: {share}\n")
                print(f"✓ 成功生成3个分片，已保存到: {args.output}")
            else:
                print("✓ 成功生成3个分片:")
                for i, share in enumerate(encoded_shares, 1):
                    print(f"Share {i}: {share}")
                print("\n⚠️  请安全保存这3个分片，任意2个即可恢复密钥")
        
        except Exception as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.command == 'combine':
        if len(args.shares) < 2:
            print("错误: 至少需要2个分片才能恢复秘密", file=sys.stderr)
            sys.exit(1)
        
        # 解码分片
        try:
            decoded_shares = []
            for share_str in args.shares:
                x, share_bytes = decode_share(share_str.strip())
                decoded_shares.append((x, share_bytes))
            
            # 恢复秘密
            secret_bytes = combine_shares(decoded_shares)
            
            # 格式化输出
            if args.format == 'hex':
                output = '0x' + secret_bytes.hex()
            elif args.format == 'base64':
                output = base64.b64encode(secret_bytes).decode('ascii')
            elif args.format == 'utf8':
                output = secret_bytes.decode('utf-8')
            
            if args.output:
                if args.format == 'hex':
                    with open(args.output, 'w') as f:
                        f.write(output + '\n')
                else:
                    with open(args.output, 'wb') as f:
                        f.write(secret_bytes)
                print(f"✓ 成功恢复秘密，已保存到: {args.output}")
            else:
                print("✓ 恢复的秘密:")
                print(output)
        
        except Exception as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()

