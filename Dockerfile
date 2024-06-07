# https://pdm-project.org/en/latest/usage/advanced/#use-pdm-in-a-multi-stage-dockerfile
FROM python:3.12

# install Firefox
RUN apt-get update && apt-get install -y firefox-esr
# install PDM
RUN pip install -U pdm
# disable update check
ENV PDM_CHECK_UPDATE=false
# copy README.md, pyproject.toml, pdm.lock, LICENSE, .pdm-python, and src/ to /app
COPY README.md pyproject.toml pdm.lock LICENSE .pdm-python src/ /app/
# set working directory to /app
WORKDIR /app
# install dependencies
RUN pdm install --prod
# set entrypoint to pdm run -- scrape-and-ntfy
ENTRYPOINT ["pdm", "run", "--", "scrape-and-ntfy", "--docker-headless"]
# ENTRYPOINT ["which", "firefox-esr"]