// Dear ImGui 样式橱窗：同一份 UI 代码，靠程序化样式系统换出四套气质。
//
// ImGui 没有样式表，一切观感都是每帧提交的参数——这个程序演示的是它的
// 「参数化美化」上限：色板、圆角、间距全在代码里，accent 色一处改动全局联动，
// 再配合 ImDrawList 手绘渐变与仪表，达到工具软件的精致观感。
//
// 本文件用 C++：ImGui 本体与 win32/dx11 后端都是 C++（ImGui 的母语），
// cimgui 的 C 绑定需要用 Lua 现场生成后端包装，不值得绕。

#include "imgui.h"
#include "imgui_internal.h" // IM_PI
#include "imgui_impl_dx11.h"
#include "imgui_impl_win32.h"
#include <d3d11.h>
#include <tchar.h>
#include <cmath>
#include <cstring>
#include <cstdio>

// 后端需要的窗口过程转发
extern IMGUI_IMPL_API LRESULT ImGui_ImplWin32_WndProcHandler(HWND hWnd, UINT msg,
                                                             WPARAM wParam, LPARAM lParam);

static ID3D11Device *g_device = nullptr;
static ID3D11DeviceContext *g_context = nullptr;
static IDXGISwapChain *g_swap = nullptr;
static ID3D11RenderTargetView *g_rtv = nullptr;

struct Theme
{
    const char *name;
    ImU32 bg;      // 窗口底
    ImU32 surface; // 卡片/子面板
    ImU32 accent;  // 主强调色
    ImU32 text;    // 正文
    bool dark;
};

static Theme kThemes[] = {
    { "暗夜紫", IM_COL32(0x14, 0x10, 0x1E, 255), IM_COL32(0x1D, 0x17, 0x30, 255),
      IM_COL32(0x8B, 0x5C, 0xF6, 255), IM_COL32(0xED, 0xE9, 0xFE, 255), true },
    { "深海青", IM_COL32(0x0B, 0x19, 0x29, 255), IM_COL32(0x12, 0x26, 0x3A, 255),
      IM_COL32(0x22, 0xD3, 0xEE, 255), IM_COL32(0xE0, 0xF2, 0xFE, 255), true },
    { "暖阳米白", IM_COL32(0xF6, 0xF2, 0xEA, 255), IM_COL32(0xFF, 0xFF, 0xFF, 255),
      IM_COL32(0xE8, 0x59, 0x0C, 255), IM_COL32(0x3A, 0x3F, 0x45, 255), false },
    { "经典暗", IM_COL32(0x0F, 0x11, 0x15, 255), IM_COL32(0x17, 0x1A, 0x21, 255),
      IM_COL32(0x4C, 0x8D, 0xFF, 255), IM_COL32(0xE6, 0xE9, 0xEF, 255), true },
};
static int g_theme = 0;

static ImU32 g_accent, g_accent_hi, g_accent_lo; // 手绘组件取色的全局副本

static ImU32 Tint(ImU32 c, float t) // t>0 提亮，t<0 压暗
{
    ImVec4 v = ImGui::ColorConvertU32ToFloat4(c);
    if (t >= 0)
    {
        v.x += (1 - v.x) * t; v.y += (1 - v.y) * t;
        v.z += (1 - v.z) * t;
    }
    else
    {
        v.x *= (1 + t); v.y *= (1 + t); v.z *= (1 + t);
    }
    return ImGui::ColorConvertFloat4ToU32(v);
}

static void ApplyTheme(int idx)
{
    g_theme = idx;
    const Theme &t = kThemes[idx];
    ImGuiStyle &s = ImGui::GetStyle();
    s.WindowRounding = 0.0f;
    s.ChildRounding = 14.0f;
    s.FrameRounding = 9.0f;
    s.PopupRounding = 12.0f;
    s.GrabRounding = 8.0f;
    s.ScrollbarRounding = 9.0f;
    s.TabRounding = 9.0f;
    s.FramePadding = ImVec2(12, 7);
    s.ItemSpacing = ImVec2(10, 9);
    s.WindowPadding = ImVec2(14, 14);
    s.ScrollbarSize = 13.0f;

    ImVec4 bg = ImGui::ColorConvertU32ToFloat4(t.bg);
    ImVec4 surface = ImGui::ColorConvertU32ToFloat4(t.surface);
    ImVec4 accent = ImGui::ColorConvertU32ToFloat4(t.accent);
    ImVec4 text = ImGui::ColorConvertU32ToFloat4(t.text);
    ImU32 accent_hi = Tint(t.accent, 0.35f);
    ImU32 accent_lo = Tint(t.accent, -0.35f);

    ImVec4 *c = s.Colors;
    c[ImGuiCol_WindowBg] = bg;
    c[ImGuiCol_ChildBg] = surface;
    c[ImGuiCol_PopupBg] = surface;
    c[ImGuiCol_Text] = text;
    c[ImGuiCol_TextDisabled] = ImGui::ColorConvertU32ToFloat4(Tint(t.text, t.dark ? -0.55f : 0.45f));
    c[ImGuiCol_Border] = ImGui::ColorConvertU32ToFloat4(Tint(t.surface, t.dark ? 0.18f : -0.08f));
    c[ImGuiCol_Separator] = c[ImGuiCol_Border];
    c[ImGuiCol_FrameBg] = bg;
    c[ImGuiCol_FrameBgHovered] = ImGui::ColorConvertU32ToFloat4(Tint(t.bg, 0.08f));
    c[ImGuiCol_FrameBgActive] = ImGui::ColorConvertU32ToFloat4(Tint(t.bg, 0.16f));
    c[ImGuiCol_Button] = accent;
    c[ImGuiCol_ButtonHovered] = ImGui::ColorConvertU32ToFloat4(Tint(t.accent, 0.2f));
    c[ImGuiCol_ButtonActive] = ImGui::ColorConvertU32ToFloat4(Tint(t.accent, -0.2f));
    c[ImGuiCol_Header] = accent;
    c[ImGuiCol_HeaderHovered] = ImGui::ColorConvertU32ToFloat4(Tint(t.accent, 0.2f));
    c[ImGuiCol_HeaderActive] = ImGui::ColorConvertU32ToFloat4(Tint(t.accent, -0.2f));
    c[ImGuiCol_CheckMark] = accent;
    c[ImGuiCol_SliderGrab] = accent;
    c[ImGuiCol_SliderGrabActive] = ImGui::ColorConvertU32ToFloat4(accent_hi);
    c[ImGuiCol_ScrollbarBg] = bg;
    c[ImGuiCol_ScrollbarGrab] = ImGui::ColorConvertU32ToFloat4(Tint(t.surface, t.dark ? 0.35f : -0.25f));
    c[ImGuiCol_PlotLines] = accent;
    c[ImGuiCol_PlotHistogram] = accent;
    c[ImGuiCol_TitleBg] = bg;
    c[ImGuiCol_TitleBgActive] = bg;
    c[ImGuiCol_NavCursor] = accent;
    c[ImGuiCol_DragDropTarget] = accent;

    g_accent = t.accent;
    g_accent_hi = accent_hi;
    g_accent_lo = accent_lo;
}

static float g_wave[128];
static float g_gauge = 0.0f;
static bool g_show_demo = false;
static int g_metrics_bps = 42;

static void DrawWaveCard(float w)
{
    for (int i = 0; i < 128; i++)
        g_wave[i] = sinf((i + (float)ImGui::GetTime() * 40) * 0.09f) * 0.5f
                    + sinf((i + (float)ImGui::GetTime() * 17) * 0.21f) * 0.3f;
    ImGui::PlotLines("##wave", g_wave, 128, 0, NULL, -1.1f, 1.1f, ImVec2(w, 88));
}

static void DrawGradientButton(const char *label, float w, float h)
{
    ImVec2 p = ImGui::GetCursorScreenPos();
    ImDrawList *dl = ImGui::GetWindowDrawList();
    dl->AddRectFilledMultiColor(ImVec2(p.x, p.y), ImVec2(p.x + w, p.y + h),
                                g_accent_lo, g_accent_hi, g_accent_hi, g_accent_lo);
    dl->AddRect(p, ImVec2(p.x + w, p.y + h), Tint(g_accent_hi, 0.25f), 10.0f);
    ImVec2 ts = ImGui::CalcTextSize(label);
    dl->AddText(ImVec2(p.x + (w - ts.x) * 0.5f, p.y + (h - ts.y) * 0.5f),
                IM_COL32(255, 255, 255, 235), label);
    ImGui::InvisibleButton(label, ImVec2(w, h));
    return;
}

static void DrawGauge(float radius)
{
    float t = (float)fmod(ImGui::GetTime() * 0.6, 2.0);
    g_gauge = (t < 1.0f ? t : 2.0f - t); // 0..1 来回摆
    ImVec2 center = ImGui::GetCursorScreenPos();
    center.x += radius + 8;
    center.y += radius + 8;
    ImDrawList *dl = ImGui::GetWindowDrawList();
    dl->PathClear();
    dl->PathArcTo(center, radius, IM_PI * 0.75f, IM_PI * 2.25f, 48);
    dl->PathStroke(Tint(g_accent, -0.6f), 0, 12.0f);
    dl->PathClear();
    dl->PathArcTo(center, radius, IM_PI * 0.75f,
                  IM_PI * 0.75f + IM_PI * 1.5f * g_gauge, 48);
    dl->PathStroke(g_accent, 0, 12.0f);
    char buf[16];
    snprintf(buf, 16, "%d%%", (int)(g_gauge * 100));
    ImVec2 ts = ImGui::CalcTextSize(buf);
    dl->AddText(ImVec2(center.x - ts.x * 0.5f, center.y - ts.y * 0.5f),
                ImGui::GetColorU32(ImGuiCol_Text), buf);
    ImGui::Dummy(ImVec2(radius * 2 + 16, radius * 2 + 16));
}

static void BuildUI()
{
    const Theme &t = kThemes[g_theme];
    ImGuiIO &io = ImGui::GetIO();
    ImGui::SetNextWindowPos(ImVec2(0, 0));
    ImGui::SetNextWindowSize(io.DisplaySize);
    ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(22, 18));
    ImGui::Begin("##lab", nullptr,
                 ImGuiWindowFlags_NoTitleBar | ImGuiWindowFlags_NoResize |
                     ImGuiWindowFlags_NoMove | ImGuiWindowFlags_NoCollapse |
                     ImGuiWindowFlags_NoSavedSettings);
    ImGui::PopStyleVar(); // WindowPadding 只在 Begin 读取时生效，随后立即出栈

    // 头部：标题 + 主题切换
    ImGui::PushFont(NULL, 30.0f);
    ImGui::TextUnformatted("参数化美化");
    ImGui::PopFont();
    ImGui::TextDisabled("同一份 UI 代码 × 四套色板 × 程序化圆角与间距——样式即代码。");
    ImGui::Spacing();
    for (int i = 0; i < 4; i++)
    {
        if (i)
            ImGui::SameLine();
        if (ImGui::RadioButton(kThemes[i].name, g_theme == i))
            ApplyTheme(i);
    }
    ImGui::Spacing();
    ImGui::SeparatorText("控件橱窗");

    float col_w = (io.DisplaySize.x - 22 * 2 - 10 * 2) / 3.0f;

    // 左列：实时波形 + 指标
    ImGui::BeginChild("left", ImVec2(col_w, 0),
                      ImGuiChildFlags_Borders | ImGuiChildFlags_AutoResizeY);
    ImGui::SeparatorText("实时信号");
    DrawWaveCard(col_w - 28);
    ImGui::Spacing();
    ImGui::SeparatorText("吞吐");
    ImGui::PushFont(NULL, 34.0f);
    ImGui::Text("%d Mb/s", g_metrics_bps);
    ImGui::PopFont();
    ImGui::TextDisabled("较昨日 +%d%%", 7 + (g_theme * 3) % 11);
    ImGui::EndChild();
    ImGui::SameLine();

    // 中列：常规控件
    ImGui::BeginChild("mid", ImVec2(col_w, 0),
                      ImGuiChildFlags_Borders | ImGuiChildFlags_AutoResizeY);
    ImGui::SeparatorText("输入与状态");
    static float v1 = 0.62f;
    static int v2 = 4;
    static bool chk[3] = { true, false, true };
    ImGui::SliderFloat("强度", &v1, 0, 1, "%.2f");
    ImGui::SliderInt("档位", &v2, 1, 8);
    ImGui::Checkbox("自适应降噪", &chk[0]);
    ImGui::Checkbox("夜间同步", &chk[1]);
    ImGui::Checkbox("遥测上报", &chk[2]);
    ImGui::ProgressBar(v1, ImVec2(-FLT_MIN, 18), "");
    static float col[4] = { 0.55f, 0.36f, 0.96f, 1.0f };
    ImGui::ColorEdit4("强调色", col, ImGuiColorEditFlags_NoInputs);
    ImGui::EndChild();
    ImGui::SameLine();

    // 右列：手绘组件
    ImGui::BeginChild("right", ImVec2(col_w, 0),
                      ImGuiChildFlags_Borders | ImGuiChildFlags_AutoResizeY);
    ImGui::SeparatorText("DrawList 手绘");
    DrawGradientButton("渐 变 主 行 动", col_w - 28, 46);
    ImGui::Spacing();
    DrawGauge(56.0f);
    ImGui::EndChild();

    ImGui::Spacing();
    if (ImGui::Button("ShowDemoWindow() —— 打开官方全量演示", ImVec2(-FLT_MIN, 40)))
        g_show_demo = !g_show_demo;
    ImGui::SameLine();
    ImGui::TextDisabled("(本程序保留官方 demo 入口)");

    ImGui::End();
    ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(8, 8));
    if (g_show_demo)
        ImGui::ShowDemoWindow(&g_show_demo);
    ImGui::PopStyleVar();
    (void)t;
}

static bool CreateDevice(HWND hwnd)
{
    DXGI_SWAP_CHAIN_DESC sd = {};
    sd.BufferCount = 2;
    sd.BufferDesc.Width = 0;
    sd.BufferDesc.Height = 0;
    sd.BufferDesc.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
    sd.BufferDesc.RefreshRate.Numerator = 60;
    sd.BufferDesc.RefreshRate.Denominator = 1;
    sd.Flags = DXGI_SWAP_CHAIN_FLAG_ALLOW_MODE_SWITCH;
    sd.BufferUsage = DXGI_USAGE_RENDER_TARGET_OUTPUT;
    sd.OutputWindow = hwnd;
    sd.SampleDesc.Count = 1;
    sd.Windowed = TRUE;
    sd.SwapEffect = DXGI_SWAP_EFFECT_DISCARD;

    UINT flags = 0;
    D3D_FEATURE_LEVEL fl;
    D3D_FEATURE_LEVEL wanted[] = { D3D_FEATURE_LEVEL_11_0, D3D_FEATURE_LEVEL_10_0 };
    if (D3D11CreateDeviceAndSwapChain(nullptr, D3D_DRIVER_TYPE_HARDWARE, nullptr, flags,
                                      wanted, 2, D3D11_SDK_VERSION, &sd, &g_swap,
                                      &g_device, &fl, &g_context) != S_OK)
        return false;
    ID3D11Texture2D *back = nullptr;
    g_swap->GetBuffer(0, IID_PPV_ARGS(&back));
    g_device->CreateRenderTargetView(back, nullptr, &g_rtv);
    back->Release();
    return true;
}

static void CleanupDevice()
{
    if (g_rtv) { g_rtv->Release(); g_rtv = nullptr; }
    if (g_swap) { g_swap->Release(); g_swap = nullptr; }
    if (g_context) { g_context->Release(); g_context = nullptr; }
    if (g_device) { g_device->Release(); g_device = nullptr; }
}

static bool g_resizing = false;

static LRESULT WINAPI WndProc(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam)
{
    if (ImGui_ImplWin32_WndProcHandler(hWnd, msg, wParam, lParam))
        return true;
    switch (msg)
    {
    case WM_SIZE:
        if (g_device && wParam != SIZE_MINIMIZED)
        {
            g_rtv->Release();
            g_swap->ResizeBuffers(0, LOWORD(lParam), HIWORD(lParam),
                                  DXGI_FORMAT_UNKNOWN, 0);
            ID3D11Texture2D *back = nullptr;
            g_swap->GetBuffer(0, IID_PPV_ARGS(&back));
            g_device->CreateRenderTargetView(back, nullptr, &g_rtv);
            back->Release();
        }
        return 0;
    case WM_ENTERSIZEMOVE: g_resizing = true; return 0;
    case WM_EXITSIZEMOVE: g_resizing = false; return 0;
    case WM_SYSCOMMAND:
        if ((wParam & 0xfff0) == SC_KEYMENU) // 不响应 Alt 菜单
            return 0;
        break;
    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProcW(hWnd, msg, wParam, lParam);
}

int main(int argc, char **argv)
{
    ImGui_ImplWin32_EnableDpiAwareness();
    WNDCLASSEXW wc = { sizeof(wc), CS_CLASSDC, WndProc, 0L, 0L,
                       GetModuleHandle(nullptr), nullptr, nullptr, nullptr, nullptr,
                       L"AthenaImguiLab", nullptr };
    RegisterClassExW(&wc);
    HWND hwnd = CreateWindowExW(0, wc.lpszClassName, L"ImGui Style Gallery",
                                WS_OVERLAPPEDWINDOW, 80, 60, 1280, 860, nullptr,
                                nullptr, wc.hInstance, nullptr);
    if (!CreateDevice(hwnd))
        return 1;

    ShowWindow(hwnd, SW_SHOWDEFAULT);
    UpdateWindow(hwnd);

    ImGui::CreateContext();
    ImGuiIO &io = ImGui::GetIO();
    io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard;
    // 微软雅黑：v1.92 动态字体按需栅格化，中文直接可用
    io.Fonts->AddFontFromFileTTF("C:\\Windows\\Fonts\\msyh.ttc", 19.0f);

    ImGui_ImplWin32_Init(hwnd);
    ImGui_ImplDX11_Init(g_device, g_context);
    ApplyTheme(0);
    if (argc > 1 && std::strcmp(argv[1], "--demo") == 0)
        g_show_demo = true; // 母体「官方 demo」入口直接带出 ShowDemoWindow()

    bool done = false;
    while (!done)
    {
        MSG msg;
        while (PeekMessageW(&msg, nullptr, 0, 0, PM_REMOVE))
        {
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
            if (msg.message == WM_QUIT)
                done = true;
        }
        if (done)
            break;
        if (g_resizing) // 拖动尺寸时跳帧，避免重入
        {
            Sleep(10);
            continue;
        }

        ImGui_ImplDX11_NewFrame();
        ImGui_ImplWin32_NewFrame();
        ImGui::NewFrame();
        BuildUI();
        ImGui::Render();

        const float clear[4] = { 0, 0, 0, 1 };
        g_context->OMSetRenderTargets(1, &g_rtv, nullptr);
        g_context->ClearRenderTargetView(g_rtv, clear);
        ImGui_ImplDX11_RenderDrawData(ImGui::GetDrawData());
        g_swap->Present(1, 0); // vsync
    }

    ImGui_ImplDX11_Shutdown();
    ImGui_ImplWin32_Shutdown();
    ImGui::DestroyContext();
    CleanupDevice();
    UnregisterClassW(wc.lpszClassName, wc.hInstance);
    return 0;
}
