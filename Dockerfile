FROM fedora:39

RUN dnf install -y --setopt=install_weak_deps=False --nodocs \
    sudo                \
    python3             \
    python3-yaml        \
    python3-openpyxl    \
    python3-pip         \
    && rm -rf /var/cache /var/log/dnf* /var/log/yum.*

RUN pip install aiogram

RUN groupadd -g 1000 mailbot \
    && useradd -ms /bin/bash -u 1000 -g mailbot mailbot

COPY app /home/mailbot/app

RUN echo "mailbot::mailbot" | chpasswd \
    && echo "mailbot ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/mailbot


USER mailbot

WORKDIR "/home/mailbot/app"

ENTRYPOINT [ "python3",  "/home/mailbot/app/bot.py" ]