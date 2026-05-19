docker build -t fastapi-test .
docker run -d -p 8000:8000 --name fastapi-container fastapi-test