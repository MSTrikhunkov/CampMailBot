FROM fedora:39

RUN dnf install -y --setopt=install_weak_deps=False --nodocs \
    sudo                \ 
    util-linux          \
    wget                \
    vim                 \
    mc                  \
    git                 \
    python3             \
    python3-yaml        \
    python3-openpyxl    \
    python3-pip         \
    && rm -rf /var/cache /var/log/dnf* /var/log/yum.*

RUN pip install aiogram

RUN groupadd -g 1000 dev \
    && useradd -ms /bin/bash -u 1000 -g dev dev

RUN echo "dev::dev" | chpasswd \
    && echo "dev ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/dev

RUN echo "alias ll='ls -alF'" | su dev -c "tee -a /home/dev/.bashrc"

USER dev

ENTRYPOINT [ "/usr/bin/bash" ]