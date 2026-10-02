#!/usr/bin/env python3
"""AthenaNAS 后台管理服务的唯一入口。

路由器（ImmortalWrt）上由 /etc/init.d/webapp 以
`/usr/bin/python3 /opt/webapp/app.py` 拉起（procd，cwd=/opt/webapp），
本机开发走 scripts/run_dev.py serve——两边都是这一个入口，部署时
init 脚本不需要任何改动。
"""

from __future__ import annotations

import os

from nas_admin import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host=os.environ.get("NAS_ADMIN_HOST", "0.0.0.0"),
        port=int(os.environ.get("NAS_ADMIN_PORT", "5000")),
        debug=False,
    )
