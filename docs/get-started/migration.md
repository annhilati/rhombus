---
title: Migration
icon: lucide/database-arrow-up
---

<h6>As of Version 0.1.0-pre5</h6>

# Migration 

## I can't find *this* density function type

Rhombus organizes its standard library in a logical and expressive way which can mean that some density function types are hidden in macros where the name wouldn't neccesarily suggest it.
Some vanilla density functions also changed names in which cases Rhombus often goes with the newer one.
These cases are listed here:

Density Function Type                        | Where located
-------------------------------------------- | --------------------------------------------------------------------
`minecraft:cache_2d` (until 118)             | Will be reimplemented in the future
`minecraft:cache_all_in_cell` (until 118)    | Will be reimplemented in the future
`minecraft:cache_once` (until 118)           | Pre-118 Implementation of `~.std.caching.cache`
`minecraft:end_islands` (until 113)          | Present in `~.std.noise` as `end_islands`
`minecraft:flat_cache` (until 118)           | Pre-118 Implementation of `~.std.maps.flatten`
`minecraft:interpolated` (until 125)         | Pre-125 Implementations of `~.std.caching.upscale`
`minecraft:invert` (until 111)               | Automatically used in exchange for `minecraft:reciprocal` in pre-111 versions
`minecraft:shifted_noise` (until 118)        | Pre-118 Implementation of `~.std.noise.noise`
`minecraft:slide` (until 10)                 | Not present and not planned
`minecraft:terrain_shaper_spline` (until 10) | Not present and not planned
`minecraft:weird_scaled_sampler` (until 104) | Present in `~.std.noise` as `weird_scaled_sampler`
`minecraft:y_clamped_gradient` (until 125)   | Pre-113 Implementation of `~.std.coords.gradient`