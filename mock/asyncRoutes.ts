// 模拟后端动态生成路由
import { defineFakeRoute } from "vite-plugin-fake-server/client";
import { system, monitor, permission, frame, tabs } from "@/router/enums";

/**
 * roles：页面级别权限，这里模拟二种 "admin"、"common"
 * admin：管理员角色
 * common：普通角色
 */

const systemManagementRouter = {
  path: "/system",
  meta: {
    icon: "ri:settings-3-line",
    title: "menus.pureSysManagement",
    rank: system
  },
  children: [
    {
      path: "/system/user/index",
      name: "SystemUser",
      meta: {
        icon: "ri:admin-line",
        title: "menus.pureUser",
        roles: ["admin"]
      }
    },
    {
      path: "/system/role/index",
      name: "SystemRole",
      meta: {
        icon: "ri:admin-fill",
        title: "menus.pureRole",
        roles: ["admin"]
      }
    },
    {
      path: "/system/menu/index",
      name: "SystemMenu",
      meta: {
        icon: "ep:menu",
        title: "menus.pureSystemMenu",
        roles: ["admin"]
      }
    },
    {
      path: "/system/dept/index",
      name: "SystemDept",
      meta: {
        icon: "ri:git-branch-line",
        title: "menus.pureDept",
        roles: ["admin"]
      }
    }
  ]
};

const systemMonitorRouter = {
  path: "/monitor",
  meta: {
    icon: "ep:monitor",
    title: "menus.pureSysMonitor",
    rank: monitor
  },
  children: [
    {
      path: "/monitor/online-user",
      component: "monitor/online/index",
      name: "OnlineUser",
      meta: {
        icon: "ri:user-voice-line",
        title: "menus.pureOnlineUser",
        roles: ["admin"]
      }
    },
    {
      path: "/monitor/login-logs",
      component: "monitor/logs/login/index",
      name: "LoginLog",
      meta: {
        icon: "ri:window-line",
        title: "menus.pureLoginLog",
        roles: ["admin"]
      }
    },
    {
      path: "/monitor/operation-logs",
      component: "monitor/logs/operation/index",
      name: "OperationLog",
      meta: {
        icon: "ri:history-fill",
        title: "menus.pureOperationLog",
        roles: ["admin"]
      }
    },
    {
      path: "/monitor/system-logs",
      component: "monitor/logs/system/index",
      name: "SystemLog",
      meta: {
        icon: "ri:file-search-line",
        title: "menus.pureSystemLog",
        roles: ["admin"]
      }
    }
  ]
};

const permissionRouter = {
  path: "/permission",
  meta: {
    title: "menus.purePermission",
    icon: "ep:lollipop",
    rank: permission
  },
  children: [
    {
      path: "/permission/page/index",
      name: "PermissionPage",
      meta: {
        title: "menus.purePermissionPage",
        roles: ["admin", "common"]
      }
    },
    {
      path: "/permission/button",
      meta: {
        title: "menus.purePermissionButton",
        roles: ["admin", "common"]
      },
      children: [
        {
          path: "/permission/button/router",
          component: "permission/button/index",
          name: "PermissionButtonRouter",
          meta: {
            title: "menus.purePermissionButtonRouter",
            auths: [
              "permission:btn:add",
              "permission:btn:edit",
              "permission:btn:delete"
            ]
          }
        },
        {
          path: "/permission/button/login",
          component: "permission/button/perms",
          name: "PermissionButtonLogin",
          meta: {
            title: "menus.purePermissionButtonLogin"
          }
        }
      ]
    }
  ]
};


const indexDesign = {
  path: "/index",
  meta: {
    // icon: "ri:links-fill",
    icon: "ep/menu",
    title: "主页",
    rank: frame
  },
    children: [
      // 主页设计
      {
        path: "/index/page",
        name: "indexPage",
        meta: {
          title: "主页",
          frameSrc: "http://127.0.0.1:5017",
          // keepAlive: true,
          roles: ["admin", "common"]
        }
      },
  ]
};


const RAGRumor = {
  path: "/RAGRumor",
  meta: {
    // icon: "ri:links-fill",
    icon: "ep/menu",
    title: "谣言检测",
    rank: frame
  },
    children: [
      // 主页设计
      {
        path: "/RAGRumor/page",
        name: "RAGRumorPage",
        meta: {
          title: "谣言检测",
          frameSrc: "http://127.0.0.1:5018",
          // keepAlive: true,
          roles: ["admin", "common"]
        }
      },
  ]
};


const VideoAnaly = {
  path: "/VideoAnaly",
  meta: {
    // icon: "ri:links-fill",
    icon: "ep/menu",
    title: "视频智能分析",
    rank: frame
  },
    children: [
      // 主页设计
      {
        path: "/VideoAnaly/page",
        name: "VideoAnalyPage",
        meta: {
          title: "视频智能分析",
          frameSrc: "http://127.0.0.1:5019",
          // keepAlive: true,
          roles: ["admin", "common"]
        }
      },
  ]
};


const MultiRumor = {
  path: "/MultiRumor",
  meta: {
    // icon: "ri:links-fill",
    icon: "ep/menu",
    title: "多模态检测",
    rank: frame
  },
    children: [
      // 主页设计
      {
        path: "/MultiRumor/page",
        name: "MultiRumorPage",
        meta: {
          title: "多模态检测",
          frameSrc: "http://127.0.0.1:5020",
          // keepAlive: true,
          roles: ["admin", "common"]
        }
      },
  ]
};

const frameRouter = {
  path: "/iframe",
  meta: {
    icon: "ri:links-fill",
    title: "智能机器人",
    rank: frame
  },
    children: [
      // 文化馆机器人 -- 线上
      {
        path: "/iframe/OnlineRobots",
        name: "FrameOnlineRobots",
        meta: {
          title: "🤵 虚假新闻智能检测机器人",
          frameSrc: "http://localhost/chat/nyEwiysX9GjxIdJE",
          keepAlive: true,
          roles: ["admin", "common"]
        }
      },

      // 文化馆机器人 -- 线下
      {
        path: "/iframe/OfflineRobots",
        name: "FrameOfflineRobots",
        meta: {
          title: "🤖 智能交互助手",
          frameSrc: "http://localhost:5002/",
          keepAlive: true,
          roles: ["admin", "common"]
        }
      },

      // 智能交互助手 参数配置
      {
        path: "/iframe/OfflineRobotsConfig",
        name: "FrameOfflineRobotsConfig",
        meta: {
          title: "🧭 机器人参数配置",
          frameSrc: "https://xiaozhi.me/console/agents",
          keepAlive: true,
          roles: ["admin", "common"]
        }
      },
  ]
};

const tabsRouter =
  {
  path: "/tabs",
  meta: {
    icon: "ri:bookmark-2-line",
    title: "menus.pureTabs",
    rank: tabs
  },
  children: [
    {
      path: "/tabs/index",
      name: "Tabs",
      meta: {
        title: "menus.pureTabs",
        roles: ["admin", "common"]
      }
    },
    // query 传参模式
    {
      path: "/tabs/query-detail",
      name: "TabQueryDetail",
      meta: {
        // 不在menu菜单中显示
        showLink: false,
        activePath: "/tabs/index",
        roles: ["admin", "common"]
      }
    },
    // params 传参模式
    {
      path: "/tabs/params-detail/:id",
      component: "params-detail",
      name: "TabParamsDetail",
      meta: {
        // 不在menu菜单中显示
        showLink: false,
        activePath: "/tabs/index",
        roles: ["admin", "common"]
      }
    }
  ]
};


export default defineFakeRoute([
  {
    url: "/get-async-routes",
    method: "get",
    response: () => {
      return {
        success: true,
        data: [
          systemManagementRouter,
          systemMonitorRouter,
          permissionRouter,
          indexDesign,
          RAGRumor,
          VideoAnaly,
          MultiRumor,
          frameRouter,
          //tabsRouter
        ]
      };
    }
  }
]);
