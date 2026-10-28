FROM python:3.11-slim-bookworm
WORKDIR /app
COPY public/ ./public/
EXPOSE 3000
WORKDIR /app/public
CMD ["python", "-m", "http.server", "3000"]