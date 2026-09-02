#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT
#endif
extern "C" EXPORT int infinity_telemetry_version() { return 790; }
extern "C" EXPORT double infinity_percent(double used, double total) {
    if (total <= 0.0) return 0.0;
    double v = used / total * 100.0;
    if (v < 0.0) return 0.0;
    if (v > 100.0) return 100.0;
    return v;
}
