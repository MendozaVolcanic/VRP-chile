function alert = MIROVA_VIIRS750_hotspot_detection( ...
    ZI_M13, ZI_M15, BOX, dayflag, sunglint)
%MIROVA_VIIRS750_HOTSPOT_DETECTION Detect thermal anomalies in VIIRS data.
%
%   ALERT = MIROVA_VIIRS750_HOTSPOT_DETECTION(ZI_M13, ZI_M15, BOX,
%   DAYFLAG, SUNGLINT) applies the core MIROVA hotspot-detection algorithm
%   to resampled VIIRS 750 m M-band radiances.
%
%   The algorithm combines:
%     1. an absolute threshold applied to the Normalized Thermal Index
%        (NTI);
%     2. a spatial-contextual test applied to NTI;
%     3. a spectral correction expressed by the Enhanced Thermal Index
%        (ETI);
%     4. a spatial-contextual test applied to ETI;
%     5. a second detection pass after removal of first-pass anomalies.
%
%   INPUTS
%     ZI_M13   Resampled VIIRS M13 spectral radiance matrix
%              [W m^-2 sr^-1 um^-1].
%
%     ZI_M15   Resampled VIIRS M15 spectral radiance matrix
%              [W m^-2 sr^-1 um^-1].
%
%     BOX      Region-of-interest mask, with the same size as ZI_M13:
%                0 = external/background region;
%                1 = inner region of interest (ROI 1);
%                2 = outer region of interest (ROI 2).
%              NaN values identify pixels excluded from the analysis.
%
%     dayflag  Acquisition flag:
%                0     = nighttime acquisition;
%                other = daytime acquisition.
%
%     sunglint Sun-glint angle [degrees]. All detections are rejected when
%              this angle is smaller than 12 degrees.
%
%   OUTPUT
%     alert    Linear indices of pixels classified as thermal anomalies.
%              An empty array indicates that no usable thermal anomaly was
%              detected, or that the scene was rejected. It must not be
%              interpreted as a measurement of zero volcanic heat flux.
%
%   TERMINOLOGY
%     ZI_NTI   Normalized Thermal Index:
%
%                  NTI = (L_MIR - L_TIR) / (L_MIR + L_TIR)
%
%     ZI_ETI   Enhanced Thermal Index. ETI is the residual between the
%              observed NTI and the spectrally predicted NTI obtained from
%              the MIR-TIR background relationship.
%
%   REQUIREMENTS
%     MATLAB R2024 or later.
%     Image Processing Toolbox is required for COLFILT.
%
%   REFERENCES
%     Coppola, D., Laiolo, M., Cigolini, C., Delle Donne, D. & Ripepe, M.
%     (2016). Enhanced volcanic hot-spot detection using MODIS IR data:
%     results from the MIROVA system. Geological Society, London, Special
%     Publications, 426, 181-205. https://doi.org/10.1144/SP426.5
%
%     Campus, A., Laiolo, M., Massimetti, F. et al. (2022). The transition
%     from MODIS to VIIRS for global volcano thermal monitoring. Sensors,
%     22, 1713. https://doi.org/10.3390/s22051713

    narginchk(5,5);

    validateattributes(ZI_M13, {'numeric'}, {'real','2d'}, ...
        mfilename, 'ZI_M13', 1);
    validateattributes(ZI_M15, {'numeric'}, ...
        {'real','2d','size',size(ZI_M13)}, mfilename, 'ZI_M15', 2);
    validateattributes(BOX, {'numeric','logical'}, ...
        {'real','2d','size',size(ZI_M13)}, mfilename, 'BOX', 3);
    validateattributes(dayflag, {'numeric','logical'}, ...
        {'real','scalar'}, mfilename, 'dayflag', 4);
    validateattributes(sunglint, {'numeric'}, ...
        {'real','scalar'}, mfilename, 'sunglint', 5);

    % Default output: An empty alert list.
    alert = [];

    %% 1. SUN-GLINT SCREENING
    % Specular reflection of sunlight may produce false MIR anomalies.
    % The operational algorithm rejects the complete detection when the
    % sun-glint angle is smaller than 12 degrees.
    if ~isfinite(sunglint) || sunglint < 12
        return
    end

%% 2. INPUT PREPARATION AND ROI MASKS

    % Double precision is required because NaN values are assigned to the
    % BOX border and to radiance/index matrices during contextual analyses.
    ZI_M13 = double(ZI_M13);
    ZI_M15 = double(ZI_M15);
    BOX = double(BOX);

    % Exclude the outermost image frame. A complete 3-by-3 neighbourhood is
    % unavailable along this border, so contextual statistics would not be
    % directly comparable with those calculated for internal pixels.
    BOX(:,[1 end]) = NaN;
    BOX([1 end],:) = NaN;

    % The BOX matrix divides the image into three spatial domains:
    %
    %   BOX == 0 : outer analysis domain surrounding the volcanic ROIs.
    %              This region is spatially distinct from ROI1, but it is
    %              tested using the same conservative NTI and ETI thresholds.
    %
    %   BOX == 1 : central volcanic ROI, generally centred on the summit area
    %              or on the expected location of persistent thermal activity.
    %              Conservative thresholds are used to limit false detections.
    %
    %   BOX == 2 : extended volcanic ROI surrounding the central region.
    %              It includes areas where weaker, distal or spatially variable
    %              thermal anomalies may occur. During nighttime acquisitions,
    %              this region is tested with more sensitive minimum thresholds.
    %
    % This BOX configuration represents the default spatial arrangement used
    % by the algorithm. For specific volcanoes, ROI1 and ROI2 can be shifted,
    % reshaped or resized to better match the expected location and spatial
    % extent of thermal anomalies. The ROIs can also be adapted to exclude
    % neighbouring active volcanoes or other persistent thermal sources that
    % fall within the 67-by-67 analysis window.
    %
    % Pixels outside the analysis domain, including the excluded image border,
    % are represented by NaN values.

    % Create multiplicative masks for the three spatial domains. Pixels
    % outside each domain remain NaN and cannot satisfy detection tests.
    maskBOX0 = NaN(size(BOX));
    maskROI1 = NaN(size(BOX));
    maskROI2 = NaN(size(BOX));

    maskBOX0(BOX == 0) = 1;
    maskROI1(BOX == 1) = 1;
    maskROI2(BOX == 2) = 1;

    excludedPixels = isnan(BOX);

    %% 3. TIR BRIGHTNESS TEMPERATURE AND COLD-PIXEL FILTER
    % Effective wavelengths retained from the operational implementation.
    wavelengthM13 = 4.05;    % VIIRS M13 MIR wavelength [um]
    wavelengthM15 = 10.763;  % VIIRS M15 TIR wavelength [um]

    % Convert M15 radiance into brightness temperature. Extremely cold TIR
    % pixels (<= 200 K) are removed because they commonly represent invalid
    % or strongly contaminated observations and would destabilize NTI.
    ZI_BT_M15 = radianceToTemperature(ZI_M15, wavelengthM15);
    extremelyColdPixels = ZI_BT_M15 <= 200;

    ZI_BT_M15(extremelyColdPixels) = NaN;
    ZI_M15(extremelyColdPixels) = NaN;

    %% 4. NORMALIZED THERMAL INDEX (NTI)
    % NTI enhances the contrast between high-temperature MIR emission and
    % the lower-temperature TIR background.
    ZI_NTI = (ZI_M13 - ZI_M15) ./ (ZI_M13 + ZI_M15);

    % Preserve the original scene-validity condition. For the standard
    % 67-by-67 scene this corresponds to requiring fewer than 2244 NaNs.
    maximumMissingPixels = floor(numel(ZI_NTI) / 2);
    if isempty(ZI_NTI) || ...
            sum(isnan(ZI_NTI(:))) >= maximumMissingPixels
        return
    end

    % Restrict NTI to the pixels included in BOX.
    ZI_NTI_ROI = ZI_NTI;
    ZI_NTI_ROI(excludedPixels) = NaN;

    %% 5. DAY/NIGHT DETECTION PARAMETERS
    % The algorithmic sequence is identical by day and night. Only the
    % absolute NTI threshold, statistical multipliers and minimum contextual
    % thresholds change to account for solar heating and reflected sunlight.
    if dayflag == 0
        absoluteNTIthreshold = -0.7;

        sigmaMultiplierROI1 = 10;
        sigmaMultiplierROI2 = 5;

        minimumNTIcontrastROI1 = 0.02;
        minimumNTIcontrastROI2 = 0.03;

        minimumETIcontrastROI1 = 0.01;
        minimumETIcontrastROI2 = 0.003;
    else
        absoluteNTIthreshold = -0.5;

        sigmaMultiplierROI1 = 15;
        sigmaMultiplierROI2 = 15;

        minimumNTIcontrastROI1 = 0.02;
        minimumNTIcontrastROI2 = 0.02;

        minimumETIcontrastROI1 = 0.02;
        minimumETIcontrastROI2 = 0.02;
    end

    %% 6. ABSOLUTE NTI TEST
    % These pixels exceed the fixed NTI threshold and are considered direct
    % thermal alerts. They are removed before estimating contextual
    % background statistics so that intense anomalies do not contaminate
    % the reference population.
    absoluteNTIalerts = find(ZI_NTI_ROI > absoluteNTIthreshold);

    %% 7. FIRST CONTEXTUAL DETECTION PASS
    % The first pass applies both the spatial NTI test and the spatial ETI
    % test after excluding only the absolute-NTI alerts.
    [alertsBOX0_pass1, alertsROI1_pass1, alertsROI2_pass1] = ...
        contextualDetectionPass( ...
            ZI_NTI_ROI, ZI_BT_M15, ZI_M15, wavelengthM13, ...
            excludedPixels, maskBOX0, maskROI1, maskROI2, ...
            absoluteNTIalerts, [], ...
            sigmaMultiplierROI1, sigmaMultiplierROI2, ...
            minimumNTIcontrastROI1, minimumNTIcontrastROI2, ...
            minimumETIcontrastROI1, minimumETIcontrastROI2);

    contextualAlertsPass1 = [ ...
        alertsBOX0_pass1; alertsROI1_pass1; alertsROI2_pass1];

    %% 8. SECOND CONTEXTUAL DETECTION PASS
    % First-pass anomalies are removed together with absolute-NTI alerts.
    % The background statistics and spectral relationship are then
    % recalculated. This iterative step improves sensitivity to weaker
    % anomalies located close to stronger hotspot pixels.
    [alertsBOX0_pass2, alertsROI1_pass2, alertsROI2_pass2] = ...
        contextualDetectionPass( ...
            ZI_NTI_ROI, ZI_BT_M15, ZI_M15, wavelengthM13, ...
            excludedPixels, maskBOX0, maskROI1, maskROI2, ...
            absoluteNTIalerts, contextualAlertsPass1, ...
            sigmaMultiplierROI1, sigmaMultiplierROI2, ...
            minimumNTIcontrastROI1, minimumNTIcontrastROI2, ...
            minimumETIcontrastROI1, minimumETIcontrastROI2);

    %% 9. FINAL ALERT SYNTHESIS
    % Preserve the concatenation order used by the original operational
    % implementation. UNIQUE is intentionally not applied here so that the
    % output remains algorithmically consistent with the source code.
    alert = [ ...
        alertsBOX0_pass1; ...
        alertsROI1_pass1; ...
        alertsROI2_pass1; ...
        absoluteNTIalerts; ...
        alertsBOX0_pass2; ...
        alertsROI1_pass2; ...
        alertsROI2_pass2];
end


function [alertsBOX0, alertsROI1, alertsROI2] = contextualDetectionPass( ...
    ZI_NTI_ROI, ZI_BT_M15, ZI_M15, wavelengthM13, ...
    excludedPixels, maskBOX0, maskROI1, maskROI2, ...
    absoluteNTIalerts, previouslyDetectedAlerts, ...
    sigmaMultiplierROI1, sigmaMultiplierROI2, ...
    minimumNTIcontrastROI1, minimumNTIcontrastROI2, ...
    minimumETIcontrastROI1, minimumETIcontrastROI2)

%CONTEXTUALDETECTIONPASS Apply one combined NTI-ETI contextual analysis.
%
%   A pixel is classified as anomalous only when it simultaneously exceeds:
%     - the local spatial contrast threshold in NTI; and
%     - the local spatial contrast threshold in ETI.
%
%   Separate thresholds are used for ROI 1/BOX 0 and ROI 2.

    alertsBOX0 = [];
    alertsROI1 = [];
    alertsROI2 = [];

    %% A. PREPARE AN ANOMALY-FREE NTI BACKGROUND POPULATION
    % Start from NTI restricted to the analysis domain, then remove pixels
    % already classified by the absolute test or by the previous pass.
    ZI_NTI_backgroundPopulation = ZI_NTI_ROI;
    ZI_NTI_backgroundPopulation(absoluteNTIalerts) = NaN;
    ZI_NTI_backgroundPopulation(previouslyDetectedAlerts) = NaN;

    % COLFILT supplies each 3-by-3 neighbourhood as one column. The local
    % anonymous function returns the NaN-omitting mean of each column.
    neighbourhoodMean = @(values) mean(values, 1, 'omitnan');

    %% B. SPATIAL-CONTEXTUAL NTI TEST
    % Estimate the local NTI background from the 3-by-3 moving window.
    ZI_NTI_localBackground = colfilt( ...
        ZI_NTI_backgroundPopulation, [3 3], 'sliding', ...
        neighbourhoodMean);
    ZI_NTI_localBackground(excludedPixels) = NaN;

    % Positive values identify pixels whose NTI is higher than the local
    % neighbourhood. This is the spatial NTI contrast used by the first
    % contextual detection criterion.
    ZI_NTI_spatialContrast = ...
        ZI_NTI_backgroundPopulation - ZI_NTI_localBackground;

    % Retain the rejection used in the operational code for strongly
    % negative residuals, which are irrelevant to hotspot detection.
    ZI_NTI_spatialContrast(ZI_NTI_spatialContrast < -0.1) = NaN;

    % Derive adaptive NTI thresholds from the scene-wide residual
    % distribution. Fixed minima prevent thresholds from becoming too low
    % in extremely homogeneous scenes.
    meanNTIcontrast = mean(ZI_NTI_spatialContrast(:), 'omitnan');
    stdNTIcontrast = std(ZI_NTI_spatialContrast(:), 0, 'omitnan');

    NTIthresholdROI1 = max( ...
        meanNTIcontrast + sigmaMultiplierROI1 .* stdNTIcontrast, ...
        minimumNTIcontrastROI1);

    NTIthresholdROI2 = max( ...
        meanNTIcontrast + sigmaMultiplierROI2 .* stdNTIcontrast, ...
        minimumNTIcontrastROI2);

    %% C. SPECTRAL BACKGROUND MODEL
    % Convert the M15 brightness temperature into the M13 radiance expected
    % if the pixel behaved as an isothermal background surface. This
    % synthetic MIR radiance contains no additional high-temperature
    % sub-pixel component.
    ZI_M13_expectedFromTIR = temperatureToRadiance( ...
        ZI_BT_M15, wavelengthM13);

    % Calculate the NTI predicted solely from the TIR-derived background.
    % This variable replaces the less explicit original name ZI_NTIapp.
    ZI_NTI_expectedFromTIR = ...
        (ZI_M13_expectedFromTIR - ZI_M15) ./ ...
        (ZI_M13_expectedFromTIR + ZI_M15);

    ZI_NTI_expectedFromTIR(absoluteNTIalerts) = NaN;
    ZI_NTI_expectedFromTIR(previouslyDetectedAlerts) = NaN;
    ZI_NTI_expectedFromTIR(excludedPixels) = NaN;

    % Fit the empirical scene-specific relationship between the predicted
    % background NTI and the observed NTI. At least three valid points are
    % needed for the second-order polynomial.
    validBackgroundFit = ...
        isfinite(ZI_NTI_expectedFromTIR) & ...
        isfinite(ZI_NTI_backgroundPopulation);

    if nnz(validBackgroundFit) < 3
        return
    end

    spectralFitCoefficients = polyfit( ...
        ZI_NTI_expectedFromTIR(validBackgroundFit), ...
        ZI_NTI_backgroundPopulation(validBackgroundFit), 2);

    % Evaluate the fitted relationship across the scene. This represents
    % the NTI expected from the local MIR-TIR background relationship.
    ZI_NTI_spectralReference = polyval( ...
        spectralFitCoefficients, ZI_NTI_expectedFromTIR);

    %% D. ENHANCED THERMAL INDEX (ETI)
    % In the terminology of Coppola et al. (2016), the residual between the
    % observed NTI and its spectral reference is the Enhanced Thermal Index.
    % Positive ETI values indicate excess MIR emission not explained by the
    % background MIR-TIR relationship.
    ZI_ETI = ...
        ZI_NTI_backgroundPopulation - ZI_NTI_spectralReference;

    %% E. SPATIAL-CONTEXTUAL ETI TEST
    % Estimate the local ETI background using the same 3-by-3 neighbourhood.
    ZI_ETI_localBackground = colfilt( ...
        ZI_ETI, [3 3], 'sliding', neighbourhoodMean);

    % Positive values indicate pixels whose ETI exceeds that of the local
    % neighbourhood. This quantity replaces the ambiguous original name
    % ZI_DNTI2 because it is a spatial contrast of ETI, not of raw NTI.
    ZI_ETI_spatialContrast = ZI_ETI - ZI_ETI_localBackground;
    ZI_ETI_spatialContrast(excludedPixels) = NaN;

    % Derive adaptive ETI thresholds, again constrained by ROI-specific
    % minimum values.
    meanETIcontrast = mean(ZI_ETI_spatialContrast(:), 'omitnan');
    stdETIcontrast = std(ZI_ETI_spatialContrast(:), 0, 'omitnan');

    ETIthresholdROI1 = max( ...
        meanETIcontrast + sigmaMultiplierROI1 .* stdETIcontrast, ...
        minimumETIcontrastROI1);

    ETIthresholdROI2 = max( ...
        meanETIcontrast + sigmaMultiplierROI2 .* stdETIcontrast, ...
        minimumETIcontrastROI2);

    %% F. COMBINED NTI-ETI CLASSIFICATION
    % A contextual alert must simultaneously pass the NTI and ETI spatial
    % contrast tests. BOX 0 and ROI 1 use the ROI-1 thresholds, whereas ROI
    % 2 uses the more permissive or restrictive ROI-2 thresholds defined
    % for the acquisition type.
    alertsBOX0 = find( ...
        (ZI_NTI_spatialContrast .* maskBOX0 > NTIthresholdROI1) & ...
        (ZI_ETI_spatialContrast .* maskBOX0 > ETIthresholdROI1));

    alertsROI1 = find( ...
        (ZI_NTI_spatialContrast .* maskROI1 > NTIthresholdROI1) & ...
        (ZI_ETI_spatialContrast .* maskROI1 > ETIthresholdROI1));

    alertsROI2 = find( ...
        (ZI_NTI_spatialContrast .* maskROI2 > NTIthresholdROI2) & ...
        (ZI_ETI_spatialContrast .* maskROI2 > ETIthresholdROI2));
end


function BT = radianceToTemperature(L, wavelengthUm)
%RADIANCETOTEMPERATURE Invert Planck's law for spectral radiance.
%
%   The constants and numerical formulation are retained from the original
%   operational MIROVA implementation to avoid changing pixels close to the
%   detection thresholds.

    h = 6.6256e-34;  % Planck constant [J s]
    c = 2.9979e8;    % speed of light [m s^-1]
    k = 1.38e-23;    % Boltzmann constant [J K^-1]

    secondRadiationConstant = (h * c) / k;
    planckNumerator = 2 * h * (c^2);
    wavelengthM = wavelengthUm .* 1e-6;

    BT = secondRadiationConstant ./ wavelengthM ./ ...
        log(planckNumerator ./ ...
        (wavelengthM.^5 .* (L .* 1e6)) + 1);
end


function L = temperatureToRadiance(T, wavelengthUm)
%TEMPERATURETORADIANCE Calculate spectral radiance using Planck's law.
%
%   The original use of 3.14 rather than MATLAB PI is intentionally
%   preserved to maintain numerical consistency with the operational code.

    h = 6.6256e-34;  % Planck constant [J s]
    c = 2.9979e8;    % speed of light [m s^-1]
    k = 1.38e-23;    % Boltzmann constant [J K^-1]

    firstRadiationConstant = 2 * 3.14 * h * (c^2);
    secondRadiationConstant = (h * c) / k;
    wavelengthM = wavelengthUm .* 1e-6;

    spectralExitance = firstRadiationConstant ./ ...
        (wavelengthM.^5 .* ...
        (exp(secondRadiationConstant ./ (wavelengthM .* T)) - 1)) .* ...
        1e-6;

    L = spectralExitance ./ 3.14;
end
