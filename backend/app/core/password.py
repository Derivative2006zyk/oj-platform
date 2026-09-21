from passlib.context import CryptContext


_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """对明文密码做 bcrypt 哈希。"""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """校验明文密码与哈希是否匹配。"""
    try:
        return _pwd_context.verify(plain, hashed)
    except Exception:
        return False