#[no_mangle]
pub extern "C" fn infinity_core_version() -> u32 { 790 }

#[no_mangle]
pub extern "C" fn infinity_route_score(priority: f64, success: f64, latency: f64, preferred: i32) -> f64 {
    let mut score = priority + success.clamp(0.0, 1.0) * 25.0 - latency.clamp(0.0, 20.0) * 1.5;
    if preferred != 0 { score += 40.0; }
    score
}

#[no_mangle]
pub extern "C" fn infinity_clamp(value: f64, low: f64, high: f64) -> f64 {
    value.max(low).min(high)
}
