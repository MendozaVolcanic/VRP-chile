%% MIROVA VIIRS 750 m example
% Run this script from the repository root or from the example directory.

clearvars
close all
clc

exampleDir = fileparts(mfilename('fullpath'));
repoDir = fileparts(exampleDir);
addpath(repoDir);

S = load(fullfile(exampleDir, 'VIIRS750_example.mat'));

% Sun-glint angle from satellite and solar geometry.
cosSunglint = ...
    cosd(S.sat_zen) .* cosd(S.sun_zen) - ...
    sind(S.sat_zen) .* sind(S.sun_zen) .* ...
    cosd(S.sun_azi - S.sat_azi);
cosSunglint = max(-1, min(1, cosSunglint));
sunglint = acosd(cosSunglint);

% 1) Thermal-anomaly detection.
alert = MIROVA_VIIRS750_hotspot_detection( ...
    S.ZI_M13, S.ZI_M15, S.BOX, S.dayflag, sunglint);

% 2) Volcanic radiant power.
[VRP_MW, npix, deltaL_MIR, ZI_M13bk] = ...
    MIROVA_VIIRS750_VRP(S.ZI_M13, alert);

fprintf('Acquisition: %s\n', S.acquisition_id);
fprintf('Sun-glint angle: %.2f deg\n', sunglint);
fprintf('Alert pixels: %d\n', npix);
fprintf('Integrated excess M13 radiance: %.6g W m^-2 sr^-1 um^-1\n', ...
    deltaL_MIR);
fprintf('VRP: %.3f MW\n', VRP_MW);

% Compact diagnostic view.
figure('Name', 'MIROVA VIIRS750 example');
imagesc(S.ZI_M13);
axis image
set(gca, 'YDir', 'normal');
colorbar
xlabel('Column');
ylabel('Row');
title('VIIRS M13 radiance and detected alert pixels');
hold on
[row, col] = ind2sub(size(S.ZI_M13), alert);
plot(col, row, 'ro', 'MarkerSize', 8, 'LineWidth', 1.5);
