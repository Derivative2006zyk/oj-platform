FROM eclipse-temurin:17-jdk-jammy

WORKDIR /workspace

# 预创建 javac 缓存目录，避免运行时写入失败
RUN mkdir -p /tmp/javac

CMD ["sh", "-c", "javac /workspace/Main.java && java -cp /workspace Main"]