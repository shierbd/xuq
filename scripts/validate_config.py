"""
配置验证工具
验证环境配置是否正确，包括数据库连接、API密钥等

运行方式:
    python scripts/validate_config.py
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import (
    DATABASE_CONFIG,
    DATABASE_URL,
    LLM_PROVIDER,
    LLM_CONFIG,
    CACHE_DIR,
    OUTPUT_DIR,
    LOG_DIR
)
from utils.logger import get_logger
from utils.exceptions import ConfigurationException

logger = get_logger(__name__)


def validate_directories():
    """验证必需的目录"""
    logger.info("验证目录结构...")

    dirs = {
        'CACHE_DIR': CACHE_DIR,
        'OUTPUT_DIR': OUTPUT_DIR,
        'LOG_DIR': LOG_DIR,
    }

    all_ok = True
    for name, path in dirs.items():
        if path.exists():
            logger.info(f"  ✓ {name}: {path}")
        else:
            logger.warning(f"  ✗ {name} 不存在，将自动创建: {path}")
            path.mkdir(parents=True, exist_ok=True)

    return True


def validate_database():
    """验证数据库配置"""
    logger.info("验证数据库配置...")

    db_type = DATABASE_CONFIG['type']
    logger.info(f"  数据库类型: {db_type}")

    if db_type == 'mysql':
        # 验证MySQL连接
        try:
            import pymysql
            connection = pymysql.connect(
                host=DATABASE_CONFIG['host'],
                port=DATABASE_CONFIG['port'],
                user=DATABASE_CONFIG['user'],
                password=DATABASE_CONFIG['password'],
                database=DATABASE_CONFIG['database'],
                charset=DATABASE_CONFIG['charset']
            )
            connection.close()
            logger.info(f"  ✓ MySQL连接成功: {DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}")
            return True
        except ImportError:
            logger.error("  ✗ pymysql未安装，请运行: pip install pymysql")
            return False
        except Exception as e:
            logger.error(f"  ✗ MySQL连接失败: {str(e)}")
            logger.info("  提示: 请检查 .env 文件中的数据库配置")
            return False

    elif db_type == 'sqlite':
        logger.info("  ✓ SQLite模式（数据库文件将自动创建）")
        return True

    else:
        logger.error(f"  ✗ 不支持的数据库类型: {db_type}")
        return False


def validate_llm():
    """验证LLM配置"""
    logger.info(f"验证LLM配置 ({LLM_PROVIDER})...")

    config = LLM_CONFIG.get(LLM_PROVIDER)
    if not config:
        logger.error(f"  ✗ 未找到LLM提供商配置: {LLM_PROVIDER}")
        return False

    # 验证API密钥
    api_key = config.get('api_key')
    if not api_key:
        logger.error(f"  ✗ {LLM_PROVIDER} API密钥未配置")
        logger.info(f"  提示: 请在 .env 文件中设置 {LLM_PROVIDER.upper()}_API_KEY")
        return False

    if api_key.startswith('your_') or api_key.startswith('sk-your-'):
        logger.warning(f"  ⚠ {LLM_PROVIDER} API密钥看起来像占位符，请替换为真实密钥")
        return False

    logger.info(f"  ✓ API密钥: {api_key[:10]}...")
    logger.info(f"  ✓ 模型: {config.get('model')}")
    logger.info(f"  ✓ Base URL: {config.get('base_url', 'N/A')}")

    # 尝试导入对应的库
    try:
        if LLM_PROVIDER == 'openai':
            import openai
            logger.info("  ✓ openai库已安装")
        elif LLM_PROVIDER == 'anthropic':
            import anthropic
            logger.info("  ✓ anthropic库已安装")
        elif LLM_PROVIDER == 'deepseek':
            import openai  # DeepSeek使用OpenAI接口
            logger.info("  ✓ openai库已安装（DeepSeek兼容）")
    except ImportError as e:
        logger.error(f"  ✗ 缺少依赖库: {str(e)}")
        logger.info("  提示: 请运行 pip install -r requirements.txt")
        return False

    return True


def validate_dependencies():
    """验证Python依赖"""
    logger.info("验证Python依赖...")

    required_packages = {
        'numpy': 'numpy',
        'pandas': 'pandas',
        'sqlalchemy': 'sqlalchemy',
        'sentence_transformers': 'sentence-transformers',
        'hdbscan': 'hdbscan',
        'streamlit': 'streamlit',
        'python-dotenv': 'dotenv',
        'tqdm': 'tqdm',
    }

    all_ok = True
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            logger.info(f"  ✓ {package_name}")
        except ImportError:
            logger.error(f"  ✗ {package_name} 未安装")
            all_ok = False

    if not all_ok:
        logger.info("\n  提示: 请运行 pip install -r requirements.txt")

    return all_ok


def main():
    """主函数"""
    logger.info("="*70)
    logger.info("配置验证工具")
    logger.info("="*70)

    results = {}

    # 验证目录
    results['directories'] = validate_directories()
    logger.info("")

    # 验证数据库
    results['database'] = validate_database()
    logger.info("")

    # 验证LLM
    results['llm'] = validate_llm()
    logger.info("")

    # 验证依赖
    results['dependencies'] = validate_dependencies()
    logger.info("")

    # 总结
    logger.info("="*70)
    if all(results.values()):
        logger.info("✅ 所有配置验证通过！")
        logger.info("")
        logger.info("下一步:")
        logger.info("  1. 初始化数据库: python init_database.py")
        logger.info("  2. 启动Web界面: python web_ui.py")
        logger.info("  3. 浏览器打开: http://localhost:8501")
    else:
        logger.error("❌ 部分配置验证失败，请根据上述提示修复")
        failed_items = [k for k, v in results.items() if not v]
        logger.error(f"失败项: {', '.join(failed_items)}")
        sys.exit(1)
    logger.info("="*70)


if __name__ == "__main__":
    main()
