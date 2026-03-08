#!/usr/bin/env python3
"""
币安网络稳定性监控系统 v1.0
高频交易基础设施监控
"""

import asyncio
import aiohttp
import time
import json
import statistics
from datetime import datetime, timedelta
from collections import deque
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BinanceNetworkMonitor:
    """
    币安网络监控器
    """
    
    # API端点配置
    ENDPOINTS = {
        'spot_ping': 'https://api.binance.com/api/v3/ping',
        'spot_time': 'https://api.binance.com/api/v3/time',
        'spot_ticker': 'https://api.binance.com/api/v3/ticker/24hr',
        'futures_ping': 'https://fapi.binance.com/fapi/v1/ping',
        'futures_time': 'https://fapi.binance.com/fapi/v1/time',
        'futures_ticker': 'https://fapi.binance.com/fapi/v1/ticker/24hr',
    }
    
    # 监控配置
    CONFIG = {
        'check_interval': 30,  # 检查间隔(秒)
        'history_size': 2880,  # 保留历史记录数(24小时@30秒)
        'latency_threshold': {
            'warning': 100,   # 警告阈值(ms)
            'critical': 500,  # 严重阈值(ms)
        },
        'availability_threshold': 99.9,  # 可用性阈值(%)
    }
    
    def __init__(self):
        self.metrics = {
            'latency': {name: deque(maxlen=self.CONFIG['history_size']) 
                       for name in self.ENDPOINTS.keys()},
            'errors': {name: deque(maxlen=self.CONFIG['history_size']) 
                      for name in self.ENDPOINTS.keys()},
            'availability': {name: {'success': 0, 'total': 0} 
                           for name in self.ENDPOINTS.keys()},
        }
        self.session = None
        self.running = False
        
    async def __aenter__(self):
        """异步上下文管理器"""
        timeout = aiohttp.ClientTimeout(total=10)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        if self.session:
            await self.session.close()
    
    async def check_endpoint(self, name, url):
        """
        检查单个端点
        """
        start_time = time.time()
        error = None
        
        try:
            async with self.session.get(url) as response:
                await response.text()
                latency = (time.time() - start_time) * 1000  # ms
                success = response.status == 200
                
        except asyncio.TimeoutError:
            latency = (time.time() - start_time) * 1000
            success = False
            error = 'TIMEOUT'
            
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            success = False
            error = str(type(e).__name__)
        
        # 记录指标
        self.metrics['latency'][name].append({
            'timestamp': datetime.now().isoformat(),
            'latency': latency,
            'success': success
        })
        
        self.metrics['errors'][name].append({
            'timestamp': datetime.now().isoformat(),
            'error': error,
            'success': success
        })
        
        # 更新可用性统计
        self.metrics['availability'][name]['total'] += 1
        if success:
            self.metrics['availability'][name]['success'] += 1
        
        return {
            'name': name,
            'latency': latency,
            'success': success,
            'error': error
        }
    
    async def run_check_cycle(self):
        """
        运行一轮检查
        """
        tasks = [
            self.check_endpoint(name, url)
            for name, url in self.ENDPOINTS.items()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if not isinstance(r, Exception)]
    
    def get_statistics(self, name, minutes=5):
        """
        获取统计信息
        """
        latency_data = list(self.metrics['latency'][name])
        
        if not latency_data:
            return None
        
        # 过滤最近N分钟的数据
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent = [d for d in latency_data 
                 if datetime.fromisoformat(d['timestamp']) > cutoff]
        
        if not recent:
            return None
        
        latencies = [d['latency'] for d in recent]
        successes = [d for d in recent if d['success']]
        
        return {
            'count': len(recent),
            'avg_latency': statistics.mean(latencies),
            'min_latency': min(latencies),
            'max_latency': max(latencies),
            'p95_latency': sorted(latencies)[int(len(latencies)*0.95)] if len(latencies) > 20 else max(latencies),
            'success_rate': len(successes) / len(recent) * 100,
        }
    
    def get_overall_status(self):
        """
        获取整体状态
        """
        status = {}
        
        for name in self.ENDPOINTS.keys():
            stats = self.get_statistics(name, minutes=5)
            if stats:
                # 判定状态
                if stats['success_rate'] < 95:
                    health = 'CRITICAL'
                elif stats['avg_latency'] > self.CONFIG['latency_threshold']['critical']:
                    health = 'CRITICAL'
                elif stats['avg_latency'] > self.CONFIG['latency_threshold']['warning']:
                    health = 'WARNING'
                else:
                    health = 'HEALTHY'
                
                status[name] = {
                    **stats,
                    'health': health
                }
        
        return status
    
    async def run_monitoring(self, duration_minutes=None):
        """
        运行监控循环
        """
        self.running = True
        start_time = time.time()
        cycle_count = 0
        
        logger.info(f"网络监控启动 - 检查间隔: {self.CONFIG['check_interval']}秒")
        
        while self.running:
            try:
                # 执行检查
                results = await self.run_check_cycle()
                cycle_count += 1
                
                # 每10个周期输出一次统计
                if cycle_count % 10 == 0:
                    status = self.get_overall_status()
                    logger.info(f"周期 {cycle_count} 完成 - 整体状态: {len(status)} 个端点")
                
                # 检查是否达到运行时长
                if duration_minutes:
                    elapsed = (time.time() - start_time) / 60
                    if elapsed >= duration_minutes:
                        logger.info(f"达到运行时长 {duration_minutes} 分钟，停止监控")
                        break
                
                # 等待下一轮
                await asyncio.sleep(self.CONFIG['check_interval'])
                
            except asyncio.CancelledError:
                logger.info("监控任务被取消")
                break
            except Exception as e:
                logger.error(f"监控循环出错: {e}")
                await asyncio.sleep(5)
        
        self.running = False
        return cycle_count
    
    def stop(self):
        """停止监控"""
        self.running = False
        logger.info("监控停止信号已发送")
    
    def export_report(self, filename=None):
        """
        导出监控报告
        """
        if not filename:
            filename = f"network_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'config': self.CONFIG,
            'overall_status': self.get_overall_status(),
            'raw_metrics': {
                name: list(self.metrics['latency'][name])
                for name in self.ENDPOINTS.keys()
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"报告已导出: {filename}")
        return filename


async def main():
    """
    主函数 - 运行监控测试
    """
    print("=" * 60)
    print("币安网络稳定性监控 v1.0")
    print("=" * 60)
    
    async with BinanceNetworkMonitor() as monitor:
        # 运行5分钟测试
        cycles = await monitor.run_monitoring(duration_minutes=5)
        
        # 输出最终统计
        print("\n" + "=" * 60)
        print("监控结果汇总")
        print("=" * 60)
        
        status = monitor.get_overall_status()
        for name, stats in status.items():
            print(f"\n{name}:")
            print(f"  健康状态: {stats['health']}")
            print(f"  平均延迟: {stats['avg_latency']:.2f}ms")
            print(f"  P95延迟: {stats['p95_latency']:.2f}ms")
            print(f"  成功率: {stats['success_rate']:.2f}%")
        
        # 导出报告
        report_file = monitor.export_report()
        print(f"\n详细报告: {report_file}")


if __name__ == '__main__':
    asyncio.run(main())
