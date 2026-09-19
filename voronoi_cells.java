package com.klinbee.moredensityfunctions.densityfunctions;


import com.klinbee.moredensityfunctions.distancemetrics.DistanceMetric;
import com.klinbee.moredensityfunctions.randomsamplers.RandomSampler;
import com.klinbee.moredensityfunctions.registration.TypedCodec;
import com.klinbee.moredensityfunctions.util.DistanceType;
import com.klinbee.moredensityfunctions.util.ExtraOctaves;
import com.klinbee.moredensityfunctions.util.Jitter;
import com.klinbee.moredensityfunctions.util.MDFMath;
import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.util.ExtraCodecs;
import net.minecraft.util.KeyDispatchDataCodec;
import net.minecraft.world.level.levelgen.DensityFunction;

public record VoronoiCells(RandomSampler randomSampler,
                           int sizeX,
                           int sizeY,
                           int sizeZ,
                           Jitter jitter,
                           DistanceMetric distanceMetric,
                           DistanceType distanceType,
                           int neighbors,
                           ExtraOctaves extraOctaves,
                           int salt)
        implements NoiseDensityFunction {

    private static final MapCodec<VoronoiCells> MAP_CODEC = RecordCodecBuilder.mapCodec(instance ->
            instance.group(
                    RandomSampler.CODEC.fieldOf("value_sampler").forGetter(VoronoiCells::randomSampler),
                    ExtraCodecs.NON_NEGATIVE_INT.fieldOf("size_x").forGetter(VoronoiCells::sizeX),
                    ExtraCodecs.NON_NEGATIVE_INT.fieldOf("size_y").forGetter(VoronoiCells::sizeY),
                    ExtraCodecs.NON_NEGATIVE_INT.fieldOf("size_z").forGetter(VoronoiCells::sizeZ),
                    Jitter.CODEC.fieldOf("jitter_sampler").forGetter(VoronoiCells::jitter),
                    DistanceMetric.CODEC.fieldOf("distance_metric").forGetter(VoronoiCells::distanceMetric),
                    DistanceType.CODEC.fieldOf("distance_type").forGetter(VoronoiCells::distanceType),
                    Codec.BOOL.fieldOf("exact").forGetter(VoronoiCells::isExact),
                    ExtraOctaves.CODEC.fieldOf("extra_octaves").orElse(ExtraOctaves.getDefault()).forGetter(VoronoiCells::extraOctaves),
                    Codec.INT.fieldOf("salt").orElse(0).forGetter(VoronoiCells::salt)
            ).apply(instance, VoronoiCells::new)
    );
    public static final TypedCodec<VoronoiCells> TYPED_CODEC = new TypedCodec<>("voronoi_cells", KeyDispatchDataCodec.of(MAP_CODEC));

    public VoronoiCells(RandomSampler randomSampler,
                        int sizeX,
                        int sizeY,
                        int sizeZ,
                        Jitter jitter,
                        DistanceMetric distanceMetric,
                        DistanceType distanceType,
                        boolean exact,
                        ExtraOctaves extraOctaves,
                        int salt) {
        this(randomSampler,
                sizeX,
                sizeY,
                sizeZ,
                jitter,
                distanceMetric,
                distanceType,
                exact ? 2 : 1, // exact = 2 neighbors = 5x5x5, otherwise = 1 neighbor = 3x3x3
                extraOctaves,
                salt
        );
    }

    private boolean isExact() {
        return neighbors == 2;
    }

    @Override
    public double eval(int x, int y, int z) {
        boolean is2D = sizeY == 0;
        if (is2D) {
            if (distanceType == DistanceType.F1) {
                return evaluate2DVoronoiF1(x, z);
            } else {
                return evaluate2DVoronoiF2(x, z);
            }
        } else {
            if (distanceType == DistanceType.F1) {
                return evaluate3DVoronoiF1(x, y, z);
            } else {
                return evaluate3DVoronoiF2(x, y, z);
            }
        }
    }

    private double evaluate2DVoronoiF1(int x, int z) {
        // divide into grid cells
        int gridX = MDFMath.safeFloorDiv(x, sizeX);
        int gridZ = MDFMath.safeFloorDiv(z, sizeZ);

        double minDistance = Double.MAX_VALUE;

        double minDistanceCellValue = 0.0D;

        // avoid new alloc
        double[] currPos = new double[]{x, 0, z};
        double[] samplePos = new double[3];

        for (int dx = -neighbors; dx <= neighbors; dx++) {
            for (int dz = -neighbors; dz <= neighbors; dz++) {

                // Skip corners on 5x5
                if (neighbors == 2 && ((dx | dz) == 2 || (dx | dz) == -2)) {
                    continue;
                }

                int neighborGridCellX = gridX + dx;
                int neighborGridCellZ = gridZ + dz;

                long sampleHash = RandomSampler.hashPosition(neighborGridCellX, 0, neighborGridCellZ, salt);

                double centerX = neighborGridCellX * sizeX + sizeX * 0.5;
                double centerZ = neighborGridCellZ * sizeZ + sizeZ * 0.5;

                double jitterX = MDFMath.safeModulo(jitter.samplerX().sample(sampleHash), sizeX) - sizeX * 0.5;
                sampleHash = RandomSampler.mix(sampleHash);
                double jitterY = MDFMath.safeModulo(jitter.samplerY().sample(sampleHash), sizeY);
                sampleHash = RandomSampler.mix(sampleHash);
                double jitterZ = MDFMath.safeModulo(jitter.samplerZ().sample(sampleHash), sizeZ) - sizeZ * 0.5;

                samplePos[0] = centerX + jitterX;
                samplePos[1] = jitterY;
                samplePos[2] = centerZ + jitterZ;

                double currDistance = distanceMetric.distance(
                        currPos,
                        samplePos
                );

                if (currDistance < minDistance) {
                    minDistance = currDistance;
                    minDistanceCellValue = randomSampler.sample(sampleHash);
                }
            }
        }

        return minDistanceCellValue;
    }

    private double evaluate3DVoronoiF1(int x, int y, int z) {
        // divide into grid cells
        int gridX = MDFMath.safeFloorDiv(x, sizeX);
        int gridY = MDFMath.safeFloorDiv(y, sizeY);
        int gridZ = MDFMath.safeFloorDiv(z, sizeZ);

        double minDistance = Double.MAX_VALUE;

        double minDistanceCellValue = 0.0D;

        // avoid new alloc
        double[] currPos = new double[]{x, y, z};
        double[] samplePos = new double[3];

        for (int dx = -neighbors; dx <= neighbors; dx++) {
            for (int dy = -neighbors; dy <= neighbors; dy++) {
                for (int dz = -neighbors; dz <= neighbors; dz++) {

                    // Skip corners on 5x5
                    if (neighbors == 2 && ((dx | dy | dz) == 2 || (dx | dy | dz) == -2)) {
                        continue;
                    }

                    int neighborGridCellX = gridX + dx;
                    int neighborGridCellY = gridY + dy;
                    int neighborGridCellZ = gridZ + dz;

                    long sampleHash = RandomSampler.hashPosition(neighborGridCellX, neighborGridCellY, neighborGridCellZ, salt);

                    double centerX = neighborGridCellX * sizeX + sizeX * 0.5;
                    double centerY = neighborGridCellY * sizeY + sizeY * 0.5;
                    double centerZ = neighborGridCellZ * sizeZ + sizeZ * 0.5;

                    double jitterX = MDFMath.safeModulo(jitter.samplerX().sample(sampleHash), sizeX) - sizeX * 0.5;
                    sampleHash = RandomSampler.mix(sampleHash);
                    double jitterY = MDFMath.safeModulo(jitter.samplerY().sample(sampleHash), sizeY) - sizeY * 0.5;
                    sampleHash = RandomSampler.mix(sampleHash);
                    double jitterZ = MDFMath.safeModulo(jitter.samplerZ().sample(sampleHash), sizeZ) - sizeZ * 0.5;

                    samplePos[0] = centerX + jitterX;
                    samplePos[1] = centerY + jitterY;
                    samplePos[2] = centerZ + jitterZ;

                    double currDistance = distanceMetric.distance(
                            currPos,
                            samplePos
                    );

                    if (currDistance < minDistance) {
                        minDistance = currDistance;
                        minDistanceCellValue = randomSampler.sample(sampleHash);
                    }
                }
            }
        }

        return minDistanceCellValue;
    }

    private double evaluate2DVoronoiF2(int x, int z) {
        // divide into grid cells
        int gridX = MDFMath.safeFloorDiv(x, sizeX);
        int gridZ = MDFMath.safeFloorDiv(z, sizeZ);

        // For F1 and F2 `DistanceType`
        double minDistance = Double.MAX_VALUE;
        double secondMinDistance = Double.MAX_VALUE;

        double minDistanceCellValue = 0.0D;
        double secondMinDistanceCellValue = 0.0D;

        // avoid new alloc
        double[] currPos = new double[]{x, 0, z};
        double[] samplePos = new double[3];

        for (int dx = -neighbors; dx <= neighbors; dx++) {
            for (int dz = -neighbors; dz <= neighbors; dz++) {

                // Skip corners on 5x5
                if (neighbors == 2 && ((dx | dz) == 2 || (dx | dz) == -2)) {
                    continue;
                }

                int neighborGridCellX = gridX + dx;
                int neighborGridCellZ = gridZ + dz;

                long sampleHash = RandomSampler.hashPosition(neighborGridCellX, 0, neighborGridCellZ, salt);

                double centerX = neighborGridCellX * sizeX + sizeX * 0.5;
                double centerZ = neighborGridCellZ * sizeZ + sizeZ * 0.5;

                double jitterX = MDFMath.safeModulo(jitter.samplerX().sample(sampleHash), sizeX) - sizeX * 0.5;
                sampleHash = RandomSampler.mix(sampleHash);
                double jitterY = MDFMath.safeModulo(jitter.samplerY().sample(sampleHash), sizeY);
                sampleHash = RandomSampler.mix(sampleHash);
                double jitterZ = MDFMath.safeModulo(jitter.samplerZ().sample(sampleHash), sizeZ) - sizeZ * 0.5;

                samplePos[0] = centerX + jitterX;
                samplePos[1] = jitterY;
                samplePos[2] = centerZ + jitterZ;

                double currDistance = distanceMetric.distance(
                        currPos,
                        samplePos
                );

                // For F1 and F2 `DistanceType`
                if (currDistance < minDistance) {
                    secondMinDistance = minDistance;
                    secondMinDistanceCellValue = minDistanceCellValue;
                    minDistance = currDistance;
                    minDistanceCellValue = randomSampler.sample(sampleHash);
                } else if (currDistance < secondMinDistance) {
                    secondMinDistance = currDistance;
                    secondMinDistanceCellValue = randomSampler.sample(sampleHash);
                }
            }
        }

        return switch (distanceType) {
            case F2 -> secondMinDistanceCellValue;
            case F2_ADD_F1 -> secondMinDistanceCellValue + minDistanceCellValue;
            case F2_SUB_F1 -> secondMinDistanceCellValue - minDistanceCellValue;
            case F2_MUL_F1 -> secondMinDistanceCellValue * minDistanceCellValue;
            case F2_DIV_F1 -> secondMinDistanceCellValue / minDistanceCellValue; // double = safe div
            default -> throw new AssertionError("MoreDFs attempted to use F1 DistanceType with F2 calculation.");
        };
    }

    private double evaluate3DVoronoiF2(int x, int y, int z) {
        // divide into grid cells
        int gridX = MDFMath.safeFloorDiv(x, sizeX);
        int gridY = MDFMath.safeFloorDiv(y, sizeY);
        int gridZ = MDFMath.safeFloorDiv(z, sizeZ);

        // For F1 and F2 `DistanceType`
        double minDistance = Double.MAX_VALUE;
        double secondMinDistance = Double.MAX_VALUE;

        double minDistanceCellValue = 0.0D;
        double secondMinDistanceCellValue = 0.0D;

        // avoid new alloc
        double[] currPos = new double[]{x, y, z};
        double[] samplePos = new double[3];

        for (int dx = -neighbors; dx <= neighbors; dx++) {
            for (int dy = -neighbors; dy <= neighbors; dy++) {
                for (int dz = -neighbors; dz <= neighbors; dz++) {

                    // Skip corners on 5x5
                    if (neighbors == 2 && ((dx | dy | dz) == 2 || (dx | dy | dz) == -2)) {
                        continue;
                    }

                    int neighborGridCellX = gridX + dx;
                    int neighborGridCellY = gridY + dy;
                    int neighborGridCellZ = gridZ + dz;

                    long sampleHash = RandomSampler.hashPosition(neighborGridCellX, neighborGridCellY, neighborGridCellZ, salt);

                    double centerX = neighborGridCellX * sizeX + sizeX * 0.5;
                    double centerY = neighborGridCellY * sizeY + sizeY * 0.5;
                    double centerZ = neighborGridCellZ * sizeZ + sizeZ * 0.5;

                    double jitterX = MDFMath.safeModulo(jitter.samplerX().sample(sampleHash), sizeX) - sizeX * 0.5;
                    sampleHash = RandomSampler.mix(sampleHash);
                    double jitterY = MDFMath.safeModulo(jitter.samplerY().sample(sampleHash), sizeY) - sizeY * 0.5;
                    sampleHash = RandomSampler.mix(sampleHash);
                    double jitterZ = MDFMath.safeModulo(jitter.samplerZ().sample(sampleHash), sizeZ) - sizeZ * 0.5;

                    samplePos[0] = centerX + jitterX;
                    samplePos[1] = centerY + jitterY;
                    samplePos[2] = centerZ + jitterZ;

                    double currDistance = distanceMetric.distance(
                            currPos,
                            samplePos
                    );

                    // For F1 and F2 `DistanceType`
                    if (currDistance < minDistance) {
                        secondMinDistance = minDistance;
                        secondMinDistanceCellValue = minDistanceCellValue;
                        minDistance = currDistance;
                        minDistanceCellValue = randomSampler.sample(sampleHash);
                    } else if (currDistance < secondMinDistance) {
                        secondMinDistance = currDistance;
                        secondMinDistanceCellValue = randomSampler.sample(sampleHash);
                    }
                }
            }
        }

        return switch (distanceType) {
            case F2 -> secondMinDistanceCellValue;
            case F2_ADD_F1 -> secondMinDistanceCellValue + minDistanceCellValue;
            case F2_SUB_F1 -> secondMinDistanceCellValue - minDistanceCellValue;
            case F2_MUL_F1 -> secondMinDistanceCellValue * minDistanceCellValue;
            case F2_DIV_F1 -> secondMinDistanceCellValue / minDistanceCellValue; // double = safe div
            default -> throw new AssertionError("MoreDFs attempted to use F1 DistanceType with F2 calculation.");
        };
    }

    @Override
    public DensityFunction mapAll(Visitor visitor) {
        return visitor.apply(
                new VoronoiCells(
                        randomSampler,
                        sizeX,
                        sizeY,
                        sizeZ,
                        jitter,
                        distanceMetric,
                        distanceType,
                        neighbors,
                        extraOctaves,
                        salt
                )
        );
    }

    // TODO: I'm about to have to change so many density functions...
    @Override
    public double minValue() {
        return Double.NEGATIVE_INFINITY;
    }

    @Override
    public double maxValue() {
        return Double.POSITIVE_INFINITY;
    }

    @Override
    public KeyDispatchDataCodec<? extends DensityFunction> codec() {
        return TYPED_CODEC.codec();
    }
}