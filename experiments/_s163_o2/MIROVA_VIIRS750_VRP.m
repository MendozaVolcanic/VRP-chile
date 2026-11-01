function [VRP_MW, npix, deltaL_MIR, ZI_M13bk] = ...
    MIROVA_VIIRS750_VRP(ZI_M13, alert)
%MIROVA_VIIRS750_VRP Calculate VIIRS volcanic radiant power.
%
%   [VRP_MW, NPIX, DELTAL_MIR, ZI_M13BK] = MIROVA_VIIRS750_VRP(
%   ZI_M13, ALERT) estimates the M13 background beneath detected thermal
%   anomalies and converts the integrated excess radiance to VRP.
%
%   INPUTS
%     ZI_M13  Resampled M13 spectral radiance [W m^-2 sr^-1 um^-1].
%     alert   Linear indices returned by MIROVA_VIIRS750_hotspot_detection.
%
%   OUTPUTS
%     VRP_MW      Volcanic radiant power [MW]. NaN when not determined.
%     npix        Number of detected alert pixels.
%     deltaL_MIR  Sum of above-background M13 radiance over alert pixels.
%     ZI_M13bk    Interpolated M13 background radiance matrix.
%
%   IMPORTANT
%     An empty ALERT produces VRP_MW = NaN, not zero. No detected alert
%     does not demonstrate zero emission: the target may be obscured or the
%     observation may otherwise be unsuitable.
%
%   REQUIREMENTS
%     MATLAB R2024a or newer (FILLMISSING2) and Image Processing Toolbox
%     (IMDILATE and STREL).

%   REFERENCES
%     Coppola, D., Laiolo, M., Cigolini, C., Delle Donne, D. & Ripepe, M.
%     (2016). Enhanced volcanic hot-spot detection using MODIS IR data:
%     results from the MIROVA system. Geological Society, London, Special
%     Publications, 426, 181-205. https://doi.org/10.1144/SP426.5
%
%     Campus, A., Laiolo, M., Massimetti, F. et al. (2022). The transition
%     from MODIS to VIIRS for global volcano thermal monitoring. Sensors,
%     22, 1713. https://doi.org/10.3390/s22051713

    narginchk(2,2);

    validateattributes(ZI_M13, {'numeric'}, {'real','2d'}, ...
        mfilename, 'ZI_M13', 1);
    validateattributes(alert, {'numeric'}, {'real','vector','integer','positive'}, ...
        mfilename, 'alert', 2);

    VRP_MW = NaN;
    npix = 0;
    deltaL_MIR = NaN;
    ZI_M13bk = [];

    if isempty(alert)
        return
    end

    if any(alert > numel(ZI_M13))
        error('MIROVA:InvalidAlertIndex', ...
            'ALERT contains indices outside the ZI_M13 matrix.');
    end

    ZI_M13 = double(ZI_M13);
    alert = alert(:);
    npix = numel(alert);

    % Remove anomalous pixels before reconstructing the local background.
    ZI_M13masked = ZI_M13;
    ZI_M13masked(alert) = NaN;

    % Expand the excluded region according to anomaly size.
    if npix <= 4
        kernelSize = 3;
    elseif npix <= 30
        kernelSize = 5;
    else
        kernelSize = 7;
    end

    exclusionMask = imdilate(isnan(ZI_M13masked), ...
        strel('square', kernelSize));
    ZI_M13masked(exclusionMask) = NaN;

    % Two-dimensional linear interpolation (MATLAB R2024a+).
    ZI_M13bk = fillmissing2(ZI_M13masked, 'linear');

    L_MIRhot = sum(ZI_M13(alert), 'omitnan');
    L_MIRbk  = sum(ZI_M13bk(alert), 'omitnan');
    deltaL_MIR = L_MIRhot - L_MIRbk;

    % MIROVA MIR conversion coefficient and nominal 750 m pixel area.
    mirCoefficient = 1.97e7;
    pixelAreaKm2 = 0.5625;

    VRP_MW = deltaL_MIR .* mirCoefficient .* pixelAreaKm2 ./ 1e6;
end
