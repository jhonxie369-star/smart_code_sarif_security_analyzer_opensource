import os
import subprocess
import logging

logger = logging.getLogger(__name__)

def get_file_author(project_path, file_path):
    """获取文件的最后提交者"""
    try:
        if not os.path.exists(os.path.join(project_path, '.git')):
            logger.debug(f"No .git directory in {project_path}")
            return None
            
        # 检查文件是否存在
        full_file_path = os.path.join(project_path, file_path)
        if not os.path.exists(full_file_path):
            logger.debug(f"File not found: {full_file_path}")
            return None
            
        # 使用git log获取文件的最后作者信息
        cmd = ['git', 'log', '-1', '--format=%an <%ae>', '--', file_path]
        result = subprocess.run(
            cmd, 
            cwd=project_path,
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            author = result.stdout.strip()
            logger.debug(f"Git file author for {file_path}: {author}")
            # 返回完整的作者信息
            return author
        else:
            logger.debug(f"No git history for {file_path}: {result.stderr}")
            
    except Exception as e:
        logger.warning(f"Failed to get git author for {file_path}: {e}")
    
    return None

def get_line_author(project_path, file_path, line_number):
    """获取特定行的作者"""
    try:
        if not os.path.exists(os.path.join(project_path, '.git')):
            logger.debug(f"No .git directory in {project_path}")
            return None
            
        # 检查文件是否存在
        full_file_path = os.path.join(project_path, file_path)
        if not os.path.exists(full_file_path):
            logger.debug(f"File not found: {full_file_path}")
            return None
            
        # 使用git blame获取特定行的作者
        cmd = ['git', 'blame', '-L', f'{line_number},{line_number}', '--porcelain', file_path]
        result = subprocess.run(
            cmd,
            cwd=project_path, 
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            author_name = None
            author_email = None
            
            for line in lines:
                if line.startswith('author '):
                    author_name = line[7:].strip()  # 去掉'author '前缀
                elif line.startswith('author-mail '):
                    author_email = line[12:].strip()  # 去掉'author-mail '前缀
                    
            if author_name:
                if author_email and author_email != '<>':
                    full_author = f"{author_name} {author_email}"
                else:
                    full_author = author_name
                logger.debug(f"Git line author for {file_path}:{line_number}: {full_author}")
                return full_author
        else:
            logger.debug(f"Git blame failed for {file_path}:{line_number}: {result.stderr}")
                    
    except Exception as e:
        logger.warning(f"Failed to get git blame for {file_path}:{line_number}: {e}")
    
    return None