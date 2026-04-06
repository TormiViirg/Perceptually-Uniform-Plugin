#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <d3d11_4.h>
#include <dxgi1_6.h>
#include <dcomp.h>
#include <wrl/client.h>
#include <cstdio>

#pragma comment(lib, "user32.lib")
#pragma comment(lib, "ole32.lib")
#pragma comment(lib, "d3d11.lib")
#pragma comment(lib, "dxgi.lib")
#pragma comment(lib, "dcomp.lib")

using Microsoft::WRL::ComPtr;

static void Fail(const char* expr, HRESULT hr)
{
    char buf[512];
    std::snprintf(buf, sizeof(buf), "%s failed: 0x%08X", expr, static_cast<unsigned>(hr));
    MessageBoxA(nullptr, buf, "overlay_dcomp_fp16", MB_ICONERROR);
    ExitProcess(1);
}

#define HR(expr) do { HRESULT _hr = (expr); if (FAILED(_hr)) Fail(#expr, _hr); } while (0)

struct App
{
    HWND hwnd{};
    UINT width{};
    UINT height{};

    ComPtr<ID3D11Device> device;
    ComPtr<ID3D11DeviceContext> context;
    ComPtr<ID3D11DeviceContext1> context1;

    ComPtr<IDXGIDevice> dxgiDevice;
    ComPtr<IDXGIFactory2> factory;

    ComPtr<IDXGISwapChain1> swapChain1;
    ComPtr<IDXGISwapChain3> swapChain3;
    ComPtr<ID3D11RenderTargetView> rtv;

    ComPtr<IDCompositionDevice> dcomp;
    ComPtr<IDCompositionTarget> target;
    ComPtr<IDCompositionVisual> visual;
};

static App g_app;

static void UpdateClientSize()
{
    RECT rc{};//left = 0 top = 0 right = width bottom = height

    GetClientRect(g_app.hwnd, &rc);

    g_app.width = static_cast<UINT>(rc.right - rc.left);
    g_app.height = static_cast<UINT>(rc.bottom - rc.top);
}

static void CreateRenderTarget()
{
    g_app.rtv.Reset();

    ComPtr<ID3D11Texture2D> backBuffer;
    HR(g_app.swapChain1->GetBuffer(0, IID_PPV_ARGS(&backBuffer)));
    HR(g_app.device->CreateRenderTargetView(backBuffer.Get(), nullptr, &g_app.rtv));
}

static void Render()
{
    if (!g_app.rtv)
        return;

    ID3D11RenderTargetView* rtvs[] = { g_app.rtv.Get() };
    g_app.context->OMSetRenderTargets(1, rtvs, nullptr);

    const float transparent[4] = { 0.f, 0.f, 0.f, 0.f };

    if (g_app.context1)
    {
        g_app.context1->ClearView(g_app.rtv.Get(), transparent, nullptr, 0);

        const int size = 160;
        const LONG left = static_cast<LONG>(static_cast<int>(g_app.width) / 2 - size / 2);
        const LONG top  = static_cast<LONG>(static_cast<int>(g_app.height) / 2 - size / 2);

        D3D11_RECT rect{};
        rect.left = left;
        rect.top = top;
        rect.right = left + size;
        rect.bottom = top + size;

        // Premultiplied alpha, with HDR/scRGB intensity > 1.0.
        // On SDR this clips; on an Advanced Color path it can appear brighter.
        const float hdrOrange[4] = { 4.0f, 0.8f, 0.15f, 1.0f };
        g_app.context1->ClearView(g_app.rtv.Get(), hdrOrange, &rect, 1);
    }
    else
    {
        // Very old fallback: whole window becomes opaque red.
        const float fallback[4] = { 1.f, 0.f, 0.f, 1.f };
        g_app.context->ClearRenderTargetView(g_app.rtv.Get(), fallback);
    }

    HR(g_app.swapChain1->Present(1, 0));
}

static void ResizeSwapChain(UINT w, UINT h)
{
    if (!g_app.swapChain1 || w == 0 || h == 0)
        return;

    ID3D11RenderTargetView* nullRTV[] = { nullptr };
    g_app.context->OMSetRenderTargets(1, nullRTV, nullptr);
    g_app.rtv.Reset();

    HR(g_app.swapChain1->ResizeBuffers(0, w, h, DXGI_FORMAT_UNKNOWN, 0));
    CreateRenderTarget();
    Render();
}

static void InitD3D()
{
    UINT flags = D3D11_CREATE_DEVICE_BGRA_SUPPORT;

    static const D3D_FEATURE_LEVEL levels[] =
    {
        D3D_FEATURE_LEVEL_11_1,
        D3D_FEATURE_LEVEL_11_0,
        D3D_FEATURE_LEVEL_10_1,
        D3D_FEATURE_LEVEL_10_0
    };

    D3D_FEATURE_LEVEL chosen{};
    HR(D3D11CreateDevice(
        nullptr,
        D3D_DRIVER_TYPE_HARDWARE,
        nullptr,
        flags,
        levels,
        ARRAYSIZE(levels),
        D3D11_SDK_VERSION,
        &g_app.device,
        &chosen,
        &g_app.context));

    HR(g_app.device.As(&g_app.dxgiDevice));
    (void)g_app.context.As(&g_app.context1);

    ComPtr<IDXGIAdapter> adapter;
    HR(g_app.dxgiDevice->GetAdapter(&adapter));
    HR(adapter->GetParent(IID_PPV_ARGS(&g_app.factory)));
}

static void InitComposition()
{
    HR(DCompositionCreateDevice(g_app.dxgiDevice.Get(), IID_PPV_ARGS(&g_app.dcomp)));
    HR(g_app.dcomp->CreateTargetForHwnd(g_app.hwnd, TRUE, &g_app.target));
    HR(g_app.dcomp->CreateVisual(&g_app.visual));
}

static void InitSwapChain()
{
    UpdateClientSize();

    DXGI_SWAP_CHAIN_DESC1 desc{};
    desc.Width = g_app.width;
    desc.Height = g_app.height;
    desc.Format = DXGI_FORMAT_R16G16B16A16_FLOAT;
    desc.Stereo = FALSE;
    desc.SampleDesc.Count = 1;
    desc.BufferUsage = DXGI_USAGE_RENDER_TARGET_OUTPUT;
    desc.BufferCount = 2;
    desc.Scaling = DXGI_SCALING_STRETCH;
    desc.SwapEffect = DXGI_SWAP_EFFECT_FLIP_SEQUENTIAL;
    desc.AlphaMode = DXGI_ALPHA_MODE_PREMULTIPLIED;

    HR(g_app.factory->CreateSwapChainForComposition(
        g_app.dxgiDevice.Get(),
        &desc,
        nullptr,
        &g_app.swapChain1));

    HR(g_app.swapChain1.As(&g_app.swapChain3));

    // FP16 swap chains default to this color space already, but tagging it explicitly
    // makes the intent clear for Advanced Color-aware rendering.
    (void)g_app.swapChain3->SetColorSpace1(DXGI_COLOR_SPACE_RGB_FULL_G10_NONE_P709);

    CreateRenderTarget();

    HR(g_app.visual->SetContent(g_app.swapChain1.Get()));
    HR(g_app.target->SetRoot(g_app.visual.Get()));
    HR(g_app.dcomp->Commit());
}

static LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam)
{
    switch (msg)
    {
    case WM_ERASEBKGND:
        return 1;

    case WM_MOUSEACTIVATE:
        return MA_NOACTIVATE;

    case WM_SIZE:
        if (wParam != SIZE_MINIMIZED)
        {
            UINT w = LOWORD(lParam);
            UINT h = HIWORD(lParam);
            if (w && h)
            {
                g_app.width = w;
                g_app.height = h;
                ResizeSwapChain(w, h);
            }
        }
        return 0;

    case WM_TIMER:
        DestroyWindow(hwnd);
        return 0;

    case WM_PAINT:
    {
        PAINTSTRUCT ps{};
        BeginPaint(hwnd, &ps);
        EndPaint(hwnd, &ps);
        Render();
        return 0;
    }

    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    }

    return DefWindowProcW(hwnd, msg, wParam, lParam);
}

int WINAPI wWinMain(HINSTANCE hInst, HINSTANCE, PWSTR, int)
{
    HR(CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED));

    const wchar_t* kClassName = L"DCompFP16OverlayDemo";

    WNDCLASSEXW wc{};
    wc.cbSize = sizeof(wc);
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInst;
    wc.lpszClassName = kClassName;

    if (!RegisterClassExW(&wc))
    {
        MessageBoxW(nullptr, L"RegisterClassExW failed.", L"overlay_dcomp_fp16", MB_ICONERROR);
        return 1;
    }

    const int windowW = 220;
    const int windowH = 220;
    const int screenX = GetSystemMetrics(SM_XVIRTUALSCREEN);
    const int screenY = GetSystemMetrics(SM_YVIRTUALSCREEN);
    const int screenW = GetSystemMetrics(SM_CXVIRTUALSCREEN);
    const int screenH = GetSystemMetrics(SM_CYVIRTUALSCREEN);

    const int x = screenX + (screenW - windowW) / 2;
    const int y = screenY + (screenH - windowH) / 2;

    g_app.hwnd = CreateWindowExW(
        WS_EX_TOPMOST |
        WS_EX_TOOLWINDOW |
        WS_EX_NOACTIVATE |
        WS_EX_NOREDIRECTIONBITMAP,
        kClassName,
        L"DComp FP16 Overlay",
        WS_POPUP,
        x, y, windowW, windowH,
        nullptr,
        nullptr,
        hInst,
        nullptr);

    if (!g_app.hwnd)
    {
        MessageBoxW(nullptr, L"CreateWindowExW failed.", L"overlay_dcomp_fp16", MB_ICONERROR);
        CoUninitialize();
        return 1;
    }

    InitD3D();
    InitComposition();
    InitSwapChain();

    ShowWindow(g_app.hwnd, SW_SHOWNOACTIVATE);
    UpdateWindow(g_app.hwnd);

    Render();

    // Auto-close after 2 seconds.
    SetTimer(g_app.hwnd, 1, 2000, nullptr);

    MSG msg{};
    while (GetMessageW(&msg, nullptr, 0, 0) > 0)
    {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }

    CoUninitialize();
    return 0;
}

/*Win32 window proc
global app state
raw handles
COM/D3D calls
pointer-y APIs
*/