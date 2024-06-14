# https://pdm-project.org/en/latest/usage/advanced/#use-pdm-in-a-multi-stage-dockerfile
FROM python:3.12

# install Firefox
# Whilst selenium should be able to download and cache browsers, it seems to be unable to do so properly in Docker
RUN apt-get update && apt-get install -y firefox-esr
# RUN apt-get update && apt-get upgrade -y
# install PDM
RUN pip install -U pdm
# disable update check
ENV PDM_CHECK_UPDATE=false
# copy README.md, pyproject.toml, pdm.lock, LICENSE, .pdm-python, and src/ to /app
COPY README.md pyproject.toml pdm.lock LICENSE .pdm-python src/ /app/
# set working directory to /app
WORKDIR /app
# Set PDM python interpreter to whatever is retruned by which python3
# https://github.com/pdm-project/pdm/issues/2943 
RUN pdm use $(which python3)
# install dependencies
RUN pdm install --prod
# set entrypoint to pdm run -- scrape-and-ntfy
# ENTRYPOINT ["pdm", "run", "--", "scrape-and-ntfy", "--headless"]
ENTRYPOINT ["pdm", "run", "--", "scrape-and-ntfy", "--headless", "--browser-path", "/usr/bin/firefox-esr", "--browser", "firefox"]
