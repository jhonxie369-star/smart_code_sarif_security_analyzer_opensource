import threading
import time
import logging
from queue import Queue
from django.conf import settings
from .models import ScanTask

logger = logging.getLogger(__name__)

class ScanQueue:
    """扫描队列管理器 - 单例模式"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.queue = Queue()
        self.current_task = None
        self.worker_thread = None
        self.running = False
        self._initialized = True
        
    def start_worker(self):
        """启动工作线程"""
        if self.worker_thread and self.worker_thread.is_alive():
            return
            
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        logger.info("扫描队列工作线程已启动")
    
    def add_task(self, scan_task_id, scanner_func):
        """添加扫描任务到队列"""
        self.queue.put((scan_task_id, scanner_func))
        logger.info(f"扫描任务 {scan_task_id} 已加入队列，当前队列长度: {self.queue.qsize()}")
        
        # 确保工作线程运行
        self.start_worker()
    
    def _worker(self):
        """工作线程主循环"""
        while self.running:
            try:
                # 获取任务（阻塞等待）
                scan_task_id, scanner_func = self.queue.get(timeout=1)
                self.current_task = scan_task_id
                
                logger.info(f"开始执行扫描任务 {scan_task_id}")
                
                try:
                    # 执行扫描
                    scanner_func()
                    logger.info(f"扫描任务 {scan_task_id} 执行完成")
                except Exception as e:
                    logger.error(f"扫描任务 {scan_task_id} 执行失败: {e}")
                    # 更新任务状态为失败
                    try:
                        task = ScanTask.objects.get(id=scan_task_id)
                        task.status = 'failed'
                        task.error_message = str(e)
                        task.save()
                    except Exception:
                        pass
                finally:
                    self.current_task = None
                    self.queue.task_done()
                    
            except Exception:
                # 队列为空或其他异常，继续循环
                continue
    
    def get_queue_status(self):
        """获取队列状态"""
        return {
            'queue_size': self.queue.qsize(),
            'current_task': self.current_task,
            'worker_running': self.worker_thread and self.worker_thread.is_alive()
        }

# 全局队列实例
scan_queue = ScanQueue()