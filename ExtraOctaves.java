package com.klinbee.moredensityfunctions.util;

import com.klinbee.moredensityfunctions.randomsamplers.RandomSampler;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.util.ExtraCodecs;

/// Used by `NoiseDensityFunction` implementations for noise layering
public record ExtraOctaves(int count,
                           double lacunarity,
                           double persistence,
                           double[] frequencies,
                           double[] amplitudes,
                           double maxAmplitude,
                           int[] offsetsX,
                           int[] offsetsY,
                           int[] offsetsZ) {

    public static final Codec<ExtraOctaves> CODEC = RecordCodecBuilder.create(instance ->
            instance.group(
                    ExtraCodecs.NON_NEGATIVE_INT.fieldOf("count").forGetter(ExtraOctaves::count),
                    Codec.DOUBLE.fieldOf("lacunarity").forGetter(ExtraOctaves::lacunarity),
                    Codec.DOUBLE.fieldOf("persistence").forGetter(ExtraOctaves::persistence)
            ).apply(instance, ExtraOctaves::tempNoSalt)
    );

    public static ExtraOctaves getDefault() {
        return new ExtraOctaves(0,
                0.0D,
                0.0D,
                null,
                null,
                0.0D,
                null,
                null,
                null);
    }

    private static ExtraOctaves tempNoSalt(int count, double lacunarity, double persistence) {
        if (count == 0) {
            return getDefault();
        }

        double[] amplitudes = computeNoiseRatios(count, persistence);
        double[] frequencies = computeNoiseRatios(count, lacunarity);
        double maxAmplitude = computeAmplitudesSum(count, persistence);

        return new ExtraOctaves(count, lacunarity, persistence, frequencies, amplitudes, maxAmplitude, null, null, null);
    }

    // To pre-compute offsets based on extra octave count
    private static int[] createOffsetsForAxis(int count, int baseSalt, int axisSalt) {
        int[] offsets = new int[count];
        long seed = RandomSampler.hashPosition(baseSalt, axisSalt, 0, 0);
        for (int i = 0; i < count; i++) {
            offsets[i] = (int) ((seed & 0x7FFFFFF));
            seed = RandomSampler.mix(seed);
        }
        return offsets;
    }

    // To pre-compute amplitudes/frequencies based on extra octave count
    private static double[] computeNoiseRatios(int octaves, double ratio) {
        double[] ratios = new double[octaves];
        double currRatio = ratio;
        for (int i = 0; i < octaves; i++) {
            ratios[i] = currRatio;
            currRatio *= ratio;
        }
        return ratios;
    }

    // To pre-compute the sum of amplitudes using a geometric sum
    private static double computeAmplitudesSum(int count, double ratio) {
        if (ratio == 1.0D) return count;
        return ratio * (StrictMath.pow(ratio, count) - 1) / (ratio - 1);
    }

    public boolean isSingleOctave() {
        return count == 0;
    }

    public ExtraOctaves finalizedWithSalt(int salt) {
        if (count == 0 || (offsetsX != null)) {
            return this;
        }

        int[] offsetX = createOffsetsForAxis(count, salt, 12345);
        int[] offsetY = createOffsetsForAxis(count, salt, 67890);
        int[] offsetZ = createOffsetsForAxis(count, salt, 24680);
        return new ExtraOctaves(count, lacunarity, persistence, frequencies, amplitudes, maxAmplitude, offsetX, offsetY, offsetZ);
    }
}