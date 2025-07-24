#!/usr/bin/env python3
"""
系統優化工具
用於清理除錯代碼、優化文件結構、檢查系統健康狀態
"""

import os
import re
import shutil
import sys
from pathlib import Path
from typing import List, Dict, Any

class SystemOptimizer:
    """系統優化器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.issues = []
        self.optimizations = []
        
    def scan_debug_code(self) -> List[Dict[str, Any]]:
        """掃描除錯代碼"""
        debug_patterns = [
            r'print\s*\(',
            r'console\.log\s*\(',
            r'debug\s*=\s*True',
            r'DEBUG\s*=\s*True',
            r'\.debug\s*\(',
        ]
        
        debug_issues = []
        python_files = list(self.project_root.rglob('*.py'))
        js_files = list(self.project_root.rglob('*.js'))
        
        for file_path in python_files + js_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for i, line in enumerate(content.split('\n'), 1):
                    for pattern in debug_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            debug_issues.append({
                                'file': str(file_path),
                                'line': i,
                                'content': line.strip(),
                                'pattern': pattern
                            })
            except Exception as e:
                print(f"無法讀取文件 {file_path}: {e}")
                
        return debug_issues
    
    def check_duplicate_files(self) -> List[Dict[str, Any]]:
        """檢查重複文件"""
        duplicates = []
        
        # 檢查應用程式文件重複
        app_files = list(self.project_root.glob('app*.py'))
        if len(app_files) > 1:
            duplicates.append({
                'type': 'app_files',
                'files': [str(f) for f in app_files],
                'suggestion': '建議保留 src/app_docker.py 作為主要入口點'
            })
            
        # 檢查備份文件
        backup_files = list(self.project_root.rglob('*.bak'))
        if backup_files:
            duplicates.append({
                'type': 'backup_files',
                'files': [str(f) for f in backup_files],
                'suggestion': '可以安全刪除 .bak 備份文件'
            })
            
        return duplicates
    
    def check_missing_files(self) -> List[Dict[str, Any]]:
        """檢查缺失的重要文件"""
        missing = []
        
        important_files = [
            'requirements.txt',
            'README.md',
            'docker/Dockerfile',
            '.gitignore',
            'src/config.py'
        ]
        
        for file_path in important_files:
            if not (self.project_root / file_path).exists():
                missing.append({
                    'file': file_path,
                    'importance': 'high' if file_path in ['requirements.txt', 'README.md'] else 'medium'
                })
                
        return missing
    
    def check_security_issues(self) -> List[Dict[str, Any]]:
        """檢查安全問題"""
        security_issues = []
        
        # 檢查硬編碼密碼
        config_files = list(self.project_root.rglob('*config*.py'))
        
        for config_file in config_files:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 檢查弱密碼
                weak_passwords = ['admin123', 'password', '123456', 'secret']
                for password in weak_passwords:
                    if password in content:
                        security_issues.append({
                            'type': 'weak_password',
                            'file': str(config_file),
                            'detail': f'發現弱密碼: {password}'
                        })
                        
            except Exception as e:
                print(f"無法檢查文件 {config_file}: {e}")
                
        return security_issues
    
    def optimize_static_files(self) -> List[str]:
        """優化靜態文件"""
        optimizations = []
        
        # 檢查未使用的靜態文件
        static_dir = self.project_root / 'static'
        if static_dir.exists():
            # 統計文件大小
            total_size = 0
            file_count = 0
            
            for file_path in static_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
                    
            optimizations.append(f"靜態文件統計: {file_count} 個文件, 總大小: {total_size / 1024:.1f} KB")
            
        return optimizations
    
    def generate_report(self) -> str:
        """生成優化報告"""
        report = ["🔍 系統優化報告", "=" * 50, ""]
        
        # 除錯代碼檢查
        debug_issues = self.scan_debug_code()
        if debug_issues:
            report.append(f"⚠️  發現 {len(debug_issues)} 個除錯代碼問題:")
            for issue in debug_issues[:10]:  # 只顯示前10個
                report.append(f"   📄 {issue['file']}:{issue['line']} - {issue['content'][:60]}...")
            if len(debug_issues) > 10:
                report.append(f"   ... 還有 {len(debug_issues) - 10} 個問題")
        else:
            report.append("✅ 沒有發現除錯代碼問題")
        
        report.append("")
        
        # 重複文件檢查
        duplicates = self.check_duplicate_files()
        if duplicates:
            report.append(f"⚠️  發現 {len(duplicates)} 組重複文件:")
            for dup in duplicates:
                report.append(f"   📂 {dup['type']}: {', '.join(dup['files'])}")
                report.append(f"      💡 {dup['suggestion']}")
        else:
            report.append("✅ 沒有發現重複文件問題")
            
        report.append("")
        
        # 安全性檢查
        security_issues = self.check_security_issues()
        if security_issues:
            report.append(f"🚨 發現 {len(security_issues)} 個安全問題:")
            for issue in security_issues:
                report.append(f"   🔐 {issue['type']}: {issue['detail']}")
        else:
            report.append("✅ 沒有發現明顯安全問題")
            
        report.append("")
        
        # 靜態文件優化
        static_optimizations = self.optimize_static_files()
        if static_optimizations:
            report.append("📊 靜態文件統計:")
            for opt in static_optimizations:
                report.append(f"   {opt}")
                
        report.append("")
        report.append("🚀 優化建議:")
        report.append("   1. 移除生產環境中的 print() 語句")
        report.append("   2. 使用環境變數存儲敏感資訊")
        report.append("   3. 定期清理備份和暫存文件")
        report.append("   4. 啟用靜態文件壓縮")
        report.append("   5. 配置適當的快取策略")
        
        return "\n".join(report)

def main():
    """主函數"""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = "."
        
    optimizer = SystemOptimizer(project_root)
    report = optimizer.generate_report()
    
    print(report)
    
    # 保存報告到文件
    report_file = Path(project_root) / "optimization_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📋 完整報告已保存到: {report_file}")

if __name__ == "__main__":
    main()
