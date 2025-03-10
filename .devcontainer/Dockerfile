# FROM python:3.12-bookworm
FROM continuumio/miniconda3
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_SYSTEM_PYTHON=1

WORKDIR /app

COPY environment.yml .
RUN conda env create -f environment.yml