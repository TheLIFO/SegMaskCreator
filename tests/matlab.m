classdef CTRegistrator < matlab.apps.AppBase

    % Properties that correspond to app components
    properties (Access = public)
        % REMOVED
    end

    % TODO: Re-make this app in Python :)

    % TODO: If settings-file exists, write default settings to file, otherwise read them.
    % This should contain as many settings as possible to avoid re-instaling the app for each minor change.

    % Supressing some warnings:
    %#ok<*ST2NM>
    %#ok<*TRYNC>
    %#ok<*AGROW>
    %#ok<*ASGLU>
    %#ok<*INUSD>
    %#ok<*NASGU>
    %#ok<*STISA>

    properties (Access = public)
        
        % Knot Data Header from e.g. "E:\LocalWorkingFolder\WAI-knotCT_OlofB\Pine\STAND3-5\PINE_Knots_Whorl_measures_MIDDLE_20230307_FINAL.xlsx"
        % This is how the header appears in Execl files, which in the Matlab-Python interaction context is in the "Python"-format. The "Matlab"-format would require: ' '->_ and '.'->''
        % If this is changed, the nrrdHeaderReadWrite.py has global variables at the very beginning that should also be updated (easy). The script will try to handle it, but better do it the right way.
        RawKnotDataHeader = {'Knot ID in database' 'KNOT NO.' 'Knot Diam' 'Azimuth' 'Knot type' 'R1' 'L1 a' 'L1 b' 'D1' 'L2' 'L3' 'L4' 'L5' 'Count 1' 'Knot start'};
        % Specify the fields that will contain strings (or other cell data).
        KnotDataCellFields = {'Knot_ID_in_database', 'Knot_type'};
        KnotDataStruct
        
        % On Linus' machine: (default values)
        nrrdHeaderReadWritePyPath = "D:\OneDrive - ltu.se\GitHub\Manual alignement of 3D CT data\CTRegistrator\CTRegistrator\python scripts\nrrdHeaderReadWrite.py";
        python_path = "C:\Users\Linus\anaconda3\envs\Matlab\python.exe";
        WAIKnotCTnrrdWrite = "D:\OneDrive - ltu.se\GitHub\Manual alignement of 3D CT data\CTRegistrator\CTRegistrator\python scripts\WAI-KnotCTnrrdWrite.py";

        % App stuff that's easier if Public
        wetVolume
        dryVolume
        sliceStep = 1;
        displayMode = 'montage';
    end

    methods (Access = private)
        %%% TODO: To store all transformations ("deformation fields"), see https://se.mathworks.com/help/images/ref/imwarp.html#btqog63-1-RB
        % This means all transformations, movement, rotations, ..., needs to be switched to something like affine3d transformations where "RB" is accumulated and stored globaly.

        function loadData(app, load_default)
            arguments
                app
                load_default logical = false
            end
            %%
            fprintf('Trying to load NRRD CT data...\n')
            app.PlotLamp.Color = [1,0,0];
            drawnow

            %%% Needs to load one wet volume and one dry. The wet volume is fixed, and the dry is moved to be matched the wet.

            % Only one Wet option:
            wetPath = GetDiskFile(app,'Wet');
            wetPath = fullfile(wetPath.folder, wetPath.name);

            % Several Dry options:
            dryOriginalPath = GetDiskFile(app,'Dry');
            dryOriginalPath = [dryOriginalPath.folder filesep dryOriginalPath.name];

            autoMatchedPath = GetDiskFile(app,'Matched automatic');
            autoMatchedPath = [autoMatchedPath.folder filesep autoMatchedPath.name];

            manualMatchedPath = GetDiskFile(app,'Matched manually');
            manualMatchedPath = [manualMatchedPath.folder filesep manualMatchedPath.name];

            % Verify agreement between all file path with .nrrd file header info: "Root Information", TODO: this is planned to be extended in the future.
            fprintf('\tFile-verification:... ')
            for path = {wetPath, dryOriginalPath, autoMatchedPath, manualMatchedPath}
                if ~isfile(path); continue; end 
                fileinfo = nrrdinfo(path);
                rootinfo = split(fileinfo.RawAttributes.rootinformation,':'); % Outputs for example: {'Pine', 'STAND3-5', 'Disks'}
                % Check to make sure all above outputs are part of path.
                if any(cellfun(@isempty, cellfun(@(x) strfind(path,x), rootinfo, 'UniformOutput',false)))
                    fprintf('FAILED\n')
                    fprintf('\t\tError in loadData(): Failed to load file!\n')
                    fprintf('\t\tRootinfo from file header:\n')
                    fprintf('\t\t\t%s\n', rootinfo{:})
                    fprintf('\t\tFile path:\n')
                    fprintf('\t\t\t%s\n', path{:})
                    beep
                    return
                end
            end
            fprintf('passed\n')


            %%% Select data. Choose dry in the priority order: manually matched > autmatically matched > original (unmatched).
            % Currently, the auto-matching isn't good enough
            dryPath = dryOriginalPath;

            % For now, use manual selection
            selection = 'Review manual match'; % Used later in this function so needs a value
            if load_default
                dryPath = dryOriginalPath;
            elseif isfile(manualMatchedPath)
                fig = uifigure;
                selection = uiconfirm(fig,'The current whorl have already been manually matched.','File already exists','Icon','warning','Options',{'Review manual match','Re-do from scratch','Cancel'}, 'DefaultOption',1,'CancelOption',3);
                delete(fig)
                switch selection
                    case 'Review manual match'
                        dryPath = manualMatchedPath;
                    case 'Re-do from scratch'
                        dryPath = dryOriginalPath;
                    case 'Cancel'
                        error('\tError in loadData(): Aborted data selection')
                end
                fprintf('\tSelection: %s\n', selection)

            elseif isfile(autoMatchedPath)
                fig = uifigure;
                selection = uiconfirm(fig,'The current whorl have already been automatically matched.','File already exists','Icon','warning','Options',{'Review auto match','Re-do from scratch','Cancel'}, 'DefaultOption',1,'CancelOption',3);
                delete(fig)
                switch selection
                    case 'Review auto match'
                        dryPath = autoMatchedPath;
                    case 'Re-do from scratch'
                        dryPath = dryOriginalPath;
                    case 'Cancel'
                        error('\tError in loadData(): Aborted data selection')
                end
                fprintf('\tSelection: %s\n', selection)

            elseif isfile(dryOriginalPath)
                dryPath = dryOriginalPath;
            else
                error('\tCould not find file to load!')
            end

            
            %%% Load data

            % TODO: Possibly add tiff read to handle more file formats (microtec and/or tiff stack folder), however, this would need changes to how knotdata is handled.

            % Load the data
            try 
                app.wetVolume = nrrdread(wetPath);
                app.dryVolume = nrrdread(dryPath);
            catch
                try
                    app.wetVolume = nrrdread(wetPath);
                    app.dryVolume = nrrdread(dryOriginalPath);
                catch
                    fprintf('\tError in loadData(): File Error. Could not find or read the file(s)!')
                    fprintf('\t\tpaths:\n')
                    fprintf('\t\t\t%s\n', wetPath)
                    fprintf('\t\t\t%s\n', dryPath)
                    beep
                    return
                end
            end

            wetindex = strfind(wetPath,'\');
            dryindex = strfind(dryPath,'\');
            fprintf('\tLoaded Wet as: %s\n',wetPath(wetindex(end-6):end))
            fprintf('\tLoaded Dry as: %s\n',dryPath(dryindex(end-6):end))
            
            %%% Make dryVolume at least as big as wetVolume to make room for transformations. Cropped to same size during SaveMathching().
            % Padds below/right in the End View.
            % Rows
            if size(app.dryVolume,1) < size(app.wetVolume,1)
                app.dryVolume = cat(1, app.dryVolume, zeros(size(app.wetVolume,1)-size(app.dryVolume,1), size(app.dryVolume,2), size(app.dryVolume,3)));
            end

            % Columns
            if size(app.dryVolume,2) < size(app.wetVolume,2)
                app.dryVolume = cat(2, app.dryVolume, zeros(size(app.dryVolume,1), size(app.wetVolume,2)-size(app.dryVolume,2), size(app.dryVolume,3)));
            end

            % Slices
            if size(app.dryVolume,3) < size(app.wetVolume,3)
                app.dryVolume = cat(3, app.dryVolume, zeros(size(app.dryVolume,1), size(app.dryVolume,2), size(app.wetVolume,3)-size(app.dryVolume,3)));
            end


            %%% Adjust app to data

            % Calibrate sliders
            app.SideDrySlider.Limits = [1 size(app.dryVolume,2)];
            app.SideWetSlider.Limits = [1 size(app.wetVolume,2)];
            app.TopDrySlider.Limits  = [1 size(app.dryVolume,1)];
            app.TopWetSlider.Limits  = [1 size(app.wetVolume,1)];
            app.EndDrySlider.Limits  = [1 size(app.dryVolume,3)];
            app.EndWetSlider.Limits  = [1 size(app.wetVolume,3)];

            % Set sliders to where the knot whorl is expected to be found.
            % Bounding Box of the discs inside their respective volumes
            bbWV=[find(max(app.dryVolume,[],[2 3])~=0,1,'first')...
                  find(max(app.dryVolume,[],[2 3])~=0,1,'last')...
                  find(max(app.dryVolume,[],[1 3])~=0,1,'first')...
                  find(max(app.dryVolume,[],[1 3])~=0,1,'last')...
                  find(max(app.dryVolume,[],[1 2])~=0,1,'first')...
                  find(max(app.dryVolume,[],[1 2])~=0,1,'last')];
            bbLV=[find(max(app.wetVolume,[],[2 3])~=0,1,'first')...
                  find(max(app.wetVolume,[],[2 3])~=0,1,'last')...
                  find(max(app.wetVolume,[],[1 3])~=0,1,'first')...
                  find(max(app.wetVolume,[],[1 3])~=0,1,'last')...
                  find(max(app.wetVolume,[],[1 2])~=0,1,'first')...
                  find(max(app.wetVolume,[],[1 2])~=0,1,'last')];

            app.SideDrySlider.Value = round(mean([bbWV(4) bbWV(3)]));
            app.TopDrySlider.Value  = round(mean([bbWV(2) bbWV(1)]));
            
            app.SideWetSlider.Value   = round(mean([bbLV(4) bbLV(3)]));
            app.TopWetSlider.Value    = round(mean([bbLV(2) bbLV(1)]));
            
            % Using the 8cm out of 25cm target to select a start slice worked poorly (high variance knot shapes). Let's find the closest density peak (probably knots).
            % Dry
            drymax = movmean(squeeze(max(app.dryVolume,[],[1 2])),19);
            [~,drylocations] = findpeaks(drymax,'MinPeakDistance',50,'MinPeakProminence',50);
            mainDryPeakIndex = dsearchn(drylocations,(1-80/250)*size(app.dryVolume,3));
            app.EndDrySlider.Value = drylocations(mainDryPeakIndex);

            % Limit slice to wet and dry ranges.
            app.EndDrySlider.Value = min(min(max(1,app.EndDrySlider.Value),app.EndDrySlider.Limits(2)),app.EndWetSlider.Limits(2));
            app.EndWetSlider.Value = app.EndDrySlider.Value;

            %%% Reset UI
            % Reset Coordinate Markings tab
            app.WetTopPointStoreEditField.Value = '';
            app.DryTopPointStoreEditField.Value = '';
            app.WetButtPointStoreEditField.Value = '';
            app.DryButtPointStoreEditField.Value = '';

            % Reset KnotsTab and Knot adjustments
            position = app.AzimuthEndViewPanel.Position;
            title = app.AzimuthEndViewPanel.Title;
            delete(app.AzimuthEndViewPanel)
            app.AzimuthEndViewPanel = uipanel('Title',title,'Position',position,'Parent',app.KnotsTab);

            position = app.KnotCrossSectionViewPanel.Position;
            title = app.KnotCrossSectionViewPanel.Title;
            delete(app.KnotCrossSectionViewPanel)
            app.KnotCrossSectionViewPanel = uipanel('Title',title,'Position',position,'Parent',app.KnotsTab);

            app.ConfirmAzimuthButton.Value = 0;
            app.KnotDropDown.Value = '1';
            app.KnotStartStoreEditField.Value = '';
            app.AzimuthEditField.Value = 0;
            app.L1aEditField.Value = 0;
            app.L1bEditField.Value = 0;
            app.DiameterEditField.Value = 0;
            app.L4EditField.Value = 0;

            % Sliders
            if strcmp(selection,'Review manual match') || strcmp(selection,'Review auto match')
                app.LockslicestogetherButton.Value = 1;
                LockslicestogetherButtonValueChanged(app, matlab.ui.eventdata.ButtonPushedData)
                updateDisplayMode(app, 'falsecolor')
            else
                app.LockslicestogetherButton.Value = 0;
                updateDisplayMode(app, 'montage')
            end

            app.TabGroup.SelectedTab = app.EndTab;
            app.SavematchedwhorlButton.BackgroundColor = [0.96 0.96 0.96];

            fprintf('\tCT data loaded successfully!\n')

            %%% Load knot data
            loadKnots(app, load_default)
        end
        
        function loadKnots(app, load_default)
            arguments
                app
                load_default logical = false
            end
            %%
            app.PlotLamp.Color = [1 0 0];
            fprintf('Trying to load Knot data...\n')
            drawnow

            %%%%%%%%%% New Python implementation %%%%%%%%%%
            % Read possible existing KnotData from the Dry file, as this
            % is the high contrast one that will be used to validate the 
            % KnotData for later mapping to the Wet file using the 
            % Displacement field (probably from manual matching).
                        
            % Used to get the folder path.
            DryDiskFile = GetDiskFile(app, 'Dry');

            % Load Knot Data from which file? 
            options = dir(fullfile(DryDiskFile.folder, '..'));
            options(logical(~strcmp({options.name},'Wet').*~strcmp({options.name},'Dry').*~strcmp({options.name},'Matched manually'))) = []; % Beautiful implementation...

            if load_default
                options(logical(~strcmp({options.name},'Dry'))) = [];
                i=1;
            else
                defaultIndex = find(strcmp({options.name}, 'Dry'));
                [i, tf] = listdlg('ListString', {options.name}, 'InitialValue', defaultIndex, 'PromptString', 'Select source of Knot Data.', 'SelectionMode', 'single', 'Name', 'File Selection');
                if ~tf; return; end
            end
            
            % File need to exist, otherwise the user might be doing something incorrect.
            DiskFile = GetDiskFile(app, options(i).name);
            if isempty(DiskFile)
                msgbox("Files don't exist to read Knot Data from.")
                error('\tTrying to load Knot Data from a file that does not exist: %s', options(i).name);
            end

            %%% nrrdHeaderReadWrite.py stuff
            % Initializes the KnotDataStruct from RawKnotDataHeader to know what fields to read.
            createKnotDataStruct(app)

            action = 'read';
            
            % JSON encode entire struct to read all fields. Providing individual fields is also possible.
            json_str = PythonFormattedFieldNamesOfKnotDataStructOrStr(app);
            json_data_to_read = jsonencode(json_str);
            % json_data_to_read = jsonencode(json_str,PrettyPrint=true);
            
            % Build the python command as a character array. All commands needs to be character arrays '...' starting and ending with double quotation marks: '"..."'
            % Console command structure:
            % ><python_path> <nrrdHeaderReadWrite.py_path> "<nrrd_file_path>" "<action>" "<json_string>"
            python_command = sprintf('"%s" "%s" "%s" "%s" %s', app.python_path, app.nrrdHeaderReadWritePyPath, fullfile(DiskFile.folder, DiskFile.name), action, json_data_to_read);
            
            % Call the custom nrrdHeaderReadWrite.py scritp
            [py_status, py_output] = system(python_command);

            % Parse and decode the JSON formatted py_output
            json_str = MatlabFormattedFieldNamesInJSONString(app, py_output);
            json_struct = jsondecode(json_str);

            if isempty(json_struct.Knot_start)
                json_struct.Knot_start = zeros(size(json_struct.KNOT_NO,1), 3);
            end

            if py_status == 1
                msgbox("Failed to load knots.")
                error("\tError in loadKnots(): nrrdHeaderReadWrite.py FAILED with code:\n\t\t%s", py_output)
            else
                if length(py_output) > 100; py_output(98:100) = '.'; end
                fprintf("\tSuccessfully read Knot data from NRRD header with output:\n\t\t%.100s\n", py_output)
                % fprintf('%s\n', jsonencode(jsondecode(py_output), 'PrettyPrint', true));
            end
            

            %%% KnotDataStruct and UI
            app.KnotDropDown.Value = '1';

            % Write json_struct to KnotDataStruct. The function below updates from UI, or from the provided struct.
            updateKnotDataStructWithUI(app, 'all', json_struct)

            %%% Write the KnotDataStruct to the UI
            updateKnotUIFromKnotDataStruct(app)
            
            %%%%%%%% End New Python implementation %%%%%%%%

            fprintf('\tKnot data loaded successfully!\n')
            app.PlotLamp.Color = [0 1 0];
            app.SaveallknotsButton.BackgroundColor = [0.96 0.96 0.96];
            ConfigureUI(app)
        end

        function updateView(app)
            %%
            % ConfigureUI controls slider values, so run first
            ConfigureUI(app)

            s = str2num(app.SlicesEditField.Value);
            if isempty(s); s = [1 1]; end
            current_log_slice = s(1);
            current_whorl_slice = s(2);

            % Bounding box
%             bbW=[find(max(DryEndSlice,[],2)~=0,1,'first')...
%                  find(max(DryEndSlice,[],2)~=0,1,'last')...
%                  find(max(DryEndSlice,[],1)~=0,1,'first')...
%                  find(max(DryEndSlice,[],1)~=0,1,'last')];
%             bbL=[find(max(WetEndSlice,[],2)~=0,1,'first')...
%                  find(max(WetEndSlice,[],2)~=0,1,'last')...
%                  find(max(WetEndSlice,[],1)~=0,1,'first')...
%                  find(max(WetEndSlice,[],1)~=0,1,'last')];

                %%% Top %%%

            %%% Dry
            if app.DiscreteXrayCheckBox.Value
                DryTopSlice = squeeze(sum(app.dryVolume,1));
            else
                DryTopSlice = squeeze(app.dryVolume(app.TopDrySlider.Value,:,:));
            end
            % Removes 99.Xth percentile such that "metal" doesn't dominate the contrast in the image.
            DryTopSlice(DryTopSlice>prctile(DryTopSlice(DryTopSlice>0),99.5,'all')) = prctile(DryTopSlice(DryTopSlice>0),99.5,'all');
            % Imshow displays doubles in the range [0-1], and rescale returns a dobule no matter the input format (could be uint16)
            DryTopSlice = rescale(DryTopSlice);
            % Remove background
            try % Fails if slice is all 0, which is fine
                [labeledImage, ~] = bwlabel(imdilate(imfill(imerode(DryTopSlice > 0.2,strel('disk',1)),'holes'),strel('disk',3)));
                blobMeasurements = regionprops(labeledImage, 'area', 'Centroid');
                [~, sortIndexes] = sort([blobMeasurements.Area]);
                binaryImage = ismember(labeledImage, sortIndexes(end)) > 0;
                DryTopSlice(~binaryImage) = 0;
            end
            % Apply Optional image manipulation techniques
            if app.ContrastCheckBox.Value; DryTopSlice = adapthisteq(DryTopSlice,'clipLimit',0.02,'Distribution','uniform'); end
            if app.BrightnessadjCheckBox.Value; DryTopSlice = imadjust(DryTopSlice, [prctile(DryTopSlice(DryTopSlice>0),4) prctile(DryTopSlice(DryTopSlice>0),98)],[]); end

            %%% Wet
            if app.DiscreteXrayCheckBox.Value
                WetTopSlice = squeeze(sum(app.wetVolume,1));
            else
                WetTopSlice = squeeze(app.wetVolume(app.TopWetSlider.Value,:,:));
            end
            % Removes 99.Xth percentile such that "metal" doesn't dominate the contrast in the image.
            WetTopSlice(WetTopSlice>prctile(WetTopSlice(WetTopSlice>0),99.5,'all')) = prctile(WetTopSlice(WetTopSlice>0),99.5,'all');
            % Imshow displays doubles in the range [0-1], and rescale returns a dobule no matter the input format (could be uint16)
            WetTopSlice = rescale(WetTopSlice);
            % Remove background
            try
                [labeledImage, ~] = bwlabel(imdilate(imfill(imerode(WetTopSlice > 0.2,strel('disk',1)),'holes'),strel('disk',3)));
                blobMeasurements = regionprops(labeledImage, 'area', 'Centroid');
                [~, sortIndexes] = sort([blobMeasurements.Area]);
                binaryImage = ismember(labeledImage, sortIndexes(end)) > 0;
                WetTopSlice(~binaryImage) = 0;
            end
            % Apply Optional image manipulation techniques
            if app.ContrastCheckBox.Value; WetTopSlice = adapthisteq(WetTopSlice,'clipLimit',0.02,'Distribution','uniform'); end
            if app.BrightnessadjCheckBox.Value; WetTopSlice   = imadjust(WetTopSlice, [prctile(WetTopSlice(WetTopSlice>0),4) prctile(WetTopSlice(WetTopSlice>0),98)],[]); end
            
            if app.LineCheckBox.Value
                DryTopSlice(:,current_whorl_slice) = 1;
                WetTopSlice(:,current_log_slice) = 1;
            end
            imshowpair(WetTopSlice,DryTopSlice,app.displayMode,'Parent',app.UIAxesTop)


                %%% Side %%%

            %%% Dry
            if app.DiscreteXrayCheckBox.Value
                DrySideSlice = squeeze(sum(app.dryVolume,2));
            else
                DrySideSlice = squeeze(app.dryVolume(:,app.SideDrySlider.Value,:));
            end
            % Removes 99.Xth percentile such that "metal" doesn't dominate the contrast in the image.
            DrySideSlice(DrySideSlice>prctile(DrySideSlice(DrySideSlice>0),99.5,'all')) = prctile(DrySideSlice(DrySideSlice>0),99.5,'all');
            % Imshow displays doubles in the range [0-1], and rescale returns a dobule no matter the input format (could be uint16)
            DrySideSlice = rescale(DrySideSlice);
            % Remove background
            try % Fails if slice is all 0, which is fine
                [labeledImage, ~] = bwlabel(imdilate(imfill(imerode(DrySideSlice > 0.2,strel('disk',1)),'holes'),strel('disk',3)));
                blobMeasurements = regionprops(labeledImage, 'area', 'Centroid');
                [~, sortIndexes] = sort([blobMeasurements.Area]);
                binaryImage = ismember(labeledImage, sortIndexes(end)) > 0;
                DrySideSlice(~binaryImage) = 0;
            end
            % Apply Optional image manipulation techniques
            if app.ContrastCheckBox.Value; DrySideSlice = adapthisteq(DrySideSlice,'clipLimit',0.02,'Distribution','uniform'); end
            if app.BrightnessadjCheckBox.Value; DrySideSlice = imadjust(DrySideSlice, [prctile(DrySideSlice(DrySideSlice>0),4) prctile(DrySideSlice(DrySideSlice>0),98)],[]); end
            
            %%% Wet
            if app.DiscreteXrayCheckBox.Value
                WetSideSlice = squeeze(sum(app.wetVolume,2));
            else
                WetSideSlice = squeeze(app.wetVolume(:,app.SideWetSlider.Value,:));
            end
            % Removes 99.Xth percentile such that "metal" doesn't dominate the contrast in the image.
            WetSideSlice(WetSideSlice>prctile(WetSideSlice(WetSideSlice>0),99.5,'all')) = prctile(WetSideSlice(WetSideSlice>0),99.5,'all');
            % Imshow displays doubles in the range [0-1], and rescale returns a dobule no matter the input format (could be uint16)
            WetSideSlice = rescale(WetSideSlice);
            % Remove background
            try % Fails if slice is all 0, which is fine
                [labeledImage, ~] = bwlabel(imdilate(imfill(imerode(WetSideSlice > 0.2,strel('disk',1)),'holes'),strel('disk',3)));
                blobMeasurements = regionprops(labeledImage, 'area', 'Centroid');
                [~, sortIndexes] = sort([blobMeasurements.Area]);
                binaryImage = ismember(labeledImage, sortIndexes(end)) > 0;
                WetSideSlice(~binaryImage) = 0;
            end
            % Apply Optional image manipulation techniques
            if app.ContrastCheckBox.Value; WetSideSlice = adapthisteq(WetSideSlice,'clipLimit',0.02,'Distribution','uniform'); end
            if app.BrightnessadjCheckBox.Value; WetSideSlice   = imadjust(WetSideSlice, [prctile(WetSideSlice(WetSideSlice>0),4) prctile(WetSideSlice(WetSideSlice>0),98)],[]); end
            
            if app.LineCheckBox.Value
                DrySideSlice(:,current_whorl_slice) = 1;
                WetSideSlice(:,current_log_slice) = 1;
            end
            imshowpair(WetSideSlice,DrySideSlice,app.displayMode,'Parent',app.UIAxesSide)


                %%% End %%%
            
            %%% Dry
            if app.DiscreteXrayCheckBox.Value
                DryEndSlice = squeeze(sum(app.dryVolume,3));
            else
                DryEndSlice = squeeze(app.dryVolume(:,:,app.EndDrySlider.Value));
            end
            % Removes 99.Xth percentile such that "metal" doesn't dominate the contrast in the image.
            DryEndSlice(DryEndSlice>prctile(DryEndSlice(DryEndSlice>0),99.5,'all')) = prctile(DryEndSlice(DryEndSlice>0),99.5,'all');
            % Imshow displays doubles in the range [0-1], and rescale returns a dobule no matter the input format (could be uint16)
            DryEndSlice = rescale(DryEndSlice);
            % Remove background
            try % Fails if slice is all 0, which is fine
                [labeledImage, ~] = bwlabel(imdilate(imfill(imerode(DryEndSlice > 0.2,strel('disk',1)),'holes'),strel('disk',3)));
                blobMeasurements = regionprops(labeledImage, 'area', 'Centroid');
                [~, sortIndexes] = sort([blobMeasurements.Area]);
                binaryImage = ismember(labeledImage, sortIndexes(end)) > 0;
                DryEndSlice(~binaryImage) = 0;
            end
            % Apply Optional image manipulation techniques
            if app.ContrastCheckBox.Value; DryEndSlice = adapthisteq(DryEndSlice,'clipLimit',0.02,'Distribution','uniform'); end
            if app.BrightnessadjCheckBox.Value; DryEndSlice = imadjust(DryEndSlice, [prctile(DryEndSlice(DryEndSlice>0),4) prctile(DryEndSlice(DryEndSlice>0),98)],[]); end
            
            %%% Wet
            if app.DiscreteXrayCheckBox.Value
                WetEndSlice = squeeze(sum(app.wetVolume,3));
            else
                WetEndSlice = squeeze(app.wetVolume(:,:,app.EndWetSlider.Value));
            end
            % Removes 99.Xth percentile such that "metal" doesn't dominate the contrast in the image.
            WetEndSlice(WetEndSlice>prctile(WetEndSlice(WetEndSlice>0),99.5,'all')) = prctile(WetEndSlice(WetEndSlice>0),99.5,'all');
            % Imshow displays doubles in the range [0-1], and rescale returns a dobule no matter the input format (could be uint16)
            WetEndSlice = rescale(WetEndSlice);
            % Remove background
            try % Fails if slice is all 0, which is fine
                [labeledImage, ~] = bwlabel(imdilate(imfill(imerode(WetEndSlice > 0.2,strel('disk',1)),'holes'),strel('disk',3)));
                blobMeasurements = regionprops(labeledImage, 'area', 'Centroid');
                [~, sortIndexes] = sort([blobMeasurements.Area]);
                binaryImage = ismember(labeledImage, sortIndexes(end)) > 0;
                WetEndSlice(~binaryImage) = 0;
            end
            % Apply Optional image manipulation techniques
            if app.ContrastCheckBox.Value; WetEndSlice = adapthisteq(WetEndSlice,'clipLimit',0.02,'Distribution','uniform'); end
            if app.BrightnessadjCheckBox.Value; WetEndSlice   = imadjust(WetEndSlice, [prctile(WetEndSlice(WetEndSlice>0),4) prctile(WetEndSlice(WetEndSlice>0),98)],[]); end

            imshowpair(WetEndSlice,DryEndSlice,app.displayMode,'Parent',app.UIAxesEnd)

            app.PlotLamp.Color = [0,1,0];
            drawnow
            focus(app.CTRegistratorUIFigure)
        end
        
        function updateDisplayMode(app, mode)
            %%
            switch mode
                case 'falsecolor'
                    app.displayMode = 'falsecolor';
                    app.FalsecolorCheckBox.Value = 1;
                    app.DifferenceCheckBox.Value = 0;
                    app.MontageCheckBox.Value = 0;
                case 'diff'
                    app.displayMode = 'diff';
                    app.FalsecolorCheckBox.Value = 0;
                    app.DifferenceCheckBox.Value = 1;
                    app.MontageCheckBox.Value = 0;
                case 'montage'
                    app.displayMode = 'montage';
                    app.FalsecolorCheckBox.Value = 0;
                    app.DifferenceCheckBox.Value = 0;
                    app.MontageCheckBox.Value = 1;
            end
            updateView(app)
        end
        
        function ConfigureUI(app)
            %% Enable everything, disable as needed below
            allEnableObj = findobj(app.CTRegistratorUIFigure,'-property','Enable');
            set(allEnableObj(isprop(allEnableObj,'Enable')),'Enable','on')

            %%% Components without a panel
            app.SelectedDryFileDropDown.Enable = 0;

            %%% Whorl position panel
            % Both Origin points needs to be set and the same, and the z-coord. need to be <50% of the size of the disc
            if isempty(app.WetTopPointStoreEditField.Value) || isempty(app.DryTopPointStoreEditField.Value)
                app.PitchPButton.Enable = 0;
                app.PitchMButton.Enable = 0;
                app.YawPButton.Enable = 0;
                app.YawMButton.Enable = 0;
            elseif str2num(app.DryTopPointSliceEditField.Value) > size(app.dryVolume,3)/2
                app.PitchPButton.Enable = 0;
                app.PitchMButton.Enable = 0;
                app.YawPButton.Enable = 0;
                app.YawMButton.Enable = 0;
            end

            if isempty(app.WetTopPointStoreEditField.Value) || isempty(app.DryTopPointStoreEditField.Value) || isempty(app.WetButtPointStoreEditField.Value) || isempty(app.DryButtPointStoreEditField.Value)
                app.RotateAssistButton.Enable = 0;
            end

            %%% End view slice control & sliders and slider buttons
            if app.LockslicestogetherButton.Value
                app.EndWetSlider.Enable = 0;
                app.EndWetSliderM.Enable = 0;
                app.EndWetSliderP.Enable = 0;
                app.TopWetSlider.Enable = 0;
                app.TopWetSliderM.Enable = 0;
                app.TopWetSliderP.Enable = 0;
                app.SideWetSlider.Enable = 0;
                app.SideWetSliderM.Enable = 0;
                app.SideWetSliderP.Enable = 0;

                app.EndDrySlider.Enable = 0;
                app.TopDrySlider.Enable = 0;
                app.SideDrySlider.Enable = 0;
            end

            %%% Automatic 2D/3D alignment assist buttons and lock buttons
            % If relevant coordinates are empty, or coordinates and slices are already the same
            if isempty(app.WetTopPointStoreEditField.Value) || isempty(app.DryTopPointStoreEditField.Value) || (strcmp(app.WetTopPointStoreEditField.Value, app.DryTopPointStoreEditField.Value) && strcmp(app.SlicesEditField.Value(1:strfind(app.SlicesEditField.Value,',')-1), app.SlicesEditField.Value(strfind(app.SlicesEditField.Value,',')+3:end)))
                app.TranslationAlign12Button.Enable = 0;
            end
            % If relevant coordinates are empty, or point coordinates are already the same
            if isempty(app.WetTopPointStoreEditField.Value) || isempty(app.DryTopPointStoreEditField.Value) || isempty(app.WetButtPointStoreEditField.Value) || isempty(app.DryButtPointStoreEditField.Value) || strcmp(app.WetButtPointStoreEditField.Value, app.DryButtPointStoreEditField.Value)
                app.RotationalAlign1234Button.Enable = 0;
            end
            if not(strcmp(app.WetTopPointStoreEditField.Value, app.DryTopPointStoreEditField.Value) && ~isempty(app.DryTopPointStoreEditField.Value))
                app.LockOriginsButton.Enable = 0;
            end
            if not(strcmp(app.WetButtPointStoreEditField.Value, app.DryButtPointStoreEditField.Value) && ~isempty(app.DryButtPointStoreEditField.Value))
                app.LockPointsButton.Enable = 0;
            end

            %%% Knot adjustment panel
            if isempty(app.KnotStartStoreEditField.Value) || any(str2num(app.KnotStartStoreEditField.Value) < 1)
                children = get(app.KnotadjustmentsPanel,'Children');
                set(children(isprop(children,'Enable')),'Enable','off')
                app.WhorlStartStoreButton.Enable = 1;
                app.KnotStartStoreEditField.Enable = 1;
            elseif ~app.ConfirmAzimuthButton.Value
                children = get(app.KnotadjustmentsPanel,'Children');
                set(children(isprop(children,'Enable')),'Enable','off')
                app.WhorlStartStoreButton.Enable = 1;
                app.KnotStartStoreEditField.Enable = 1;
                app.ConfirmAzimuthButton.Enable = 1;
                app.AzimuthEditField.Enable = 1;
                app.AzimuthEditFieldLabel.Enable = 1;
                app.AzimuthMButton.Enable = 1;
                app.AzimuthPButton.Enable = 1;
                app.UpdateKnotMarkingsButton.Enable = 1;
            else
                children = get(app.KnotadjustmentsPanel,'Children');
                set(children(isprop(children,'Enable')),'Enable','on')
            end

            if ~app.DeadCheckBox.Value % If knot is Green, L1a controls L1b also but let's not limit the user(?)
                % Looks-like-disabled
                % app.L1bEditField.BackgroundColor = [0.96 0.96 0.96];
                % app.L1bPButton.BackgroundColor = [0.96 0.96 0.96];
                % app.L1bMButton.BackgroundColor = [0.96 0.96 0.96];
                app.L1bEditField.Enable = 0;
                app.L1bPButton.Enable = 0;
                app.L1bMButton.Enable = 0;
            end

            app.KnotstartxyzLabel.Enable = 1;
            app.DeadCheckBox.Enable = 1;
            app.KnotDropDown.Enable = 1;
            app.KnotDropDownLabel.Enable = 1;
            app.NextKnotButton.Enable = 1;
            app.SaveallknotsButton.Enable = 1;

            if strcmp(app.KnotDropDown.Value, app.KnotDropDown.Items{end})
                app.NextKnotButton.Enable = 0;
            end

            %%% Sliders & Slices
            SideWhorlSlider_change    =   (size(app.dryVolume,2) - app.SideDrySlider.Limits(2))/2;
            app.SideDrySlider.Limits  = [1 size(app.dryVolume,2)];
            app.SideDrySlider.Value   = round(app.SideDrySlider.Value + SideWhorlSlider_change);

            TopWhorlSlider_change     =   (size(app.dryVolume,1) - app.TopDrySlider.Limits(2))/2;
            app.TopDrySlider.Limits   = [1 size(app.dryVolume,1)];
            app.TopDrySlider.Value    = round(app.TopDrySlider.Value + TopWhorlSlider_change);

            EndWhorlSlider_change     =   (size(app.dryVolume,3) - app.EndDrySlider.Limits(2)); % Special case since changes in direction 3 only happends on one side, not both.
            app.EndDrySlider.Limits   = [1 size(app.dryVolume,3)];
            app.EndDrySlider.Value    = round(app.EndDrySlider.Value + EndWhorlSlider_change);

            app.SlicesEditField.Value = sprintf('%.0f,  %.0f', app.EndWetSlider.Value, app.EndDrySlider.Value);
            slices = str2num(app.SlicesEditField.Value);
            wetSlice = slices(1);
            drySlice = slices(2);

            %%% UI changes to highlight information to the user
            % Matching coordinates and slices
            if strcmp(app.WetTopPointStoreEditField.Value, app.DryTopPointStoreEditField.Value) && ~isempty(app.DryTopPointStoreEditField.Value) && wetSlice == drySlice
                app.WetTopPointStoreButton.BackgroundColor = [0.5961 0.9843 0.5961]; % 'Pale Green'
                app.DryTopPointStoreButton.BackgroundColor = [0.5961 0.9843 0.5961];
            else
                app.WetTopPointStoreButton.BackgroundColor = [0.96 0.96 0.96]; % Matlab grey
                app.DryTopPointStoreButton.BackgroundColor = [0.96 0.96 0.96];
            end

            if strcmp(app.WetButtPointStoreEditField.Value, app.DryButtPointStoreEditField.Value) && ~isempty(app.DryButtPointStoreEditField.Value) && wetSlice == drySlice
                app.WetButtPointStoreButton.BackgroundColor = [0.5961 0.9843 0.5961];
                app.DryButtPointStoreButton.BackgroundColor = [0.5961 0.9843 0.5961];
            else
                app.WetButtPointStoreButton.BackgroundColor = [0.96 0.96 0.96];
                app.DryButtPointStoreButton.BackgroundColor = [0.96 0.96 0.96];
            end

            if wetSlice == drySlice
                app.SlicesEditField.BackgroundColor = [0.5961 0.9843 0.5961];
            else
                app.SlicesEditField.BackgroundColor = [1 1 1];
            end

            app.PlotLamp.Color = [0 1 0];
            focus(app.CTRegistratorUIFigure)
        end
        
        function maskWhorl(app)
            app.dryVolume(app.dryVolume < 0) = 0; % Some negative values appear, probably due to 'cubic'
        end
        
        function adjustSliceDifference(app)
            % Check if the user is viewing different slices, which might mean that the user thinks they have aligned the bodies but forgot to press the 'app.TranslationAlign12Button' (or ctrl+1) button.
            if ~strcmp(app.SlicesEditField.Value(1:strfind(app.SlicesEditField.Value,',')-1), app.SlicesEditField.Value(strfind(app.SlicesEditField.Value,',')+3:end)) % +3 due to white space in text box
                fig = uifigure;
                selection = uiconfirm(fig,'Your current End view shows different slices from the Wet and Dry bodies. Do you want to align them before continuing?','Missaligned sclices','Icon','warning');
                delete(fig)
                switch selection
                    case 'OK'
                        x = num2str(round(size(app.dryVolume, 1)/2));
                        y = num2str(round(size(app.dryVolume, 2)/2));
                        slices = str2num(app.SlicesEditField.Value);
                        app.WetTopPointStoreEditField.Value = sprintf('%s,  %s', x, y);
                        app.WetTopPointSliceEditField.Value = sprintf('%s', num2str(slices(1)));
                        app.DryTopPointStoreEditField.Value = sprintf('%s,  %s', x, y);
                        app.DryTopPointSliceEditField.Value = sprintf('%s', num2str(slices(2)));
                        TranslateWetTopToDryTopIn3D(app)
                    case 'Cancel'
                        fprintf('aborted\n')
                        return
                end
            end

            updateView(app)
        end

        function DiskFile = GetDiskFile(app, type, IDnumbers)
            % type: 'string' with the content one of the folder names from .../Prep/, meaning: 'Dry', 'Wet', 'Matched automatic', 'Matched manually', ...
            % IDnumbers: '1x2 cell array' with content, for example, {'07', '1'}
            if ~exist('IDnumbers','var'); IDnumbers = regexp(app.SelectedWetFileDropDown.Value,'\d*','match'); end
            DiskFile = dir([fullfile(app.SelectDataFolderButton.Text,'Disks', ['Tree ' IDnumbers{1}], 'Prep', type) filesep '*.' IDnumbers{2} '.*']);
        end

        function output = PythonFormattedFieldNamesOfKnotDataStructOrStr(app, input_str)
            % Takes the app.KnotDataStruct field names (containging e.g. '_') and converts them to the format used in the NRRD files (e.g. ' 'instead of '_').
            % Optionally, if a json_str is provided, perform the same manipulations on that string and return a string.
            % If this code is changed, make sure to update 'MatlabFormattedFieldNamesInJSONString'.
            % Check if a JSON string is provided
            if nargin > 1
                % Work directly with the provided JSON string
                json_str = input_str;
            else
                % Convert the app.KnotDataStruct to a JSON string to work with
                json_str = jsonencode(app.KnotDataStruct);
            end

            % Extract the field names based on whether a JSON string was provided
            if nargin > 1
                % Decode the provided JSON string just to extract field names
                tempStruct = jsondecode(json_str);
                header = fieldnames(tempStruct);
            else
                % Use the existing field names from app.KnotDataStruct
                header = fieldnames(app.KnotDataStruct);
            end

            % Loop over each field name and edit it in the JSON string
            for i = 1:length(header)
                oldFieldName = ['"' header{i} '"']; % JSON field names are enclosed in quotes.
                newFieldName = strrep(header{i}, '_', ' ');
                if strcmp(newFieldName, 'KNOT NO')
                    newFieldName = [newFieldName '.'];
                end
                newFieldName = ['"' newFieldName '"']; % Enclose the new field name in quotes.
                
                % Replace in the JSON string
                json_str = strrep(json_str, oldFieldName, newFieldName);
            end

            output = json_str;
        end

        function json_str = MatlabFormattedFieldNamesInJSONString(app, json_str)
            % Parses the JSON string such that the field names does not contain spaces or periods.
            % Make sure to keep this functionality up to date with changes made to 'PythonFormattedFieldNamesFromKnotDataStruct'.

            % Explenation: Match >1 quoted (") characters, that are themselves not quotes ("), that always preceeds a colon (:).
            pattern = '"[^"]+":';
            
            matches = regexp(json_str, pattern, 'match');  % Extract matched keys
            
            for i = 1:length(matches)
                oldKey = matches{i}(2:end-2);  % Remove quotes and colon
                newKey = strrep(strrep(oldKey, ' ', '_'), '.', '');  % Replace space with underscore and remove period
                json_str = strrep(json_str, oldKey, newKey);  % Replace old key with new key
            end
        end
        
        function createKnotDataStruct(app)
            %% Initializes the KnotDataStruct
            app.KnotDataStruct = struct;
            
            header = app.RawKnotDataHeader;
            
            for i = 1:length(header)
                fieldName = strrep(header{i}, ' ', '_');
                fieldName = strrep(fieldName, '.', ''); % Remove dots from name to prevent field-level confusion.
                
                if ismember(fieldName, app.KnotDataCellFields)
                    % Initialize string fields with empty cell arrays
                    app.KnotDataStruct.(fieldName) = {};
                else
                    % Initialize numerical fields with NaN to represent uninitialized numeric data
                    app.KnotDataStruct.(fieldName) = NaN;
                end
            end  
        end

        function updateKnotDataStructWithUI(app, iknot, newStruct)
            %% If newStruct is provided, overwrite the app.KnotDataStruct with this information, otherwise, read the numbers from the UI.
            if ~isfield(app.KnotDataStruct, 'KNOT_NO')
                error('Error in updateKnotDataStructWithUI(): Atempting to write data to un-initialized KnotDataStruct!')
            end
            app.SaveallknotsButton.BackgroundColor = [0.96 0.96 0.96];

            if nargin > 2
                if strcmp(iknot, 'all')
                    % Complete overwrite with newStruct
                    for fieldNameCell = fieldnames(newStruct).'
                        fieldName = cell2mat(fieldNameCell);
                        app.KnotDataStruct.(fieldName) = newStruct.(fieldName);
                    
                        % Check and convert to cell array if necessary: jsondecode prefers to treat empty data or array data as arrays while we sometimes need cell arrays.
                        if ismember(fieldName, app.KnotDataCellFields)
                            if isempty(app.KnotDataStruct.(fieldName))
                                app.KnotDataStruct.(fieldName) = {};
                            elseif ~iscell(app.KnotDataStruct.(fieldName))
                                app.KnotDataStruct.(fieldName) = {app.KnotDataStruct.(fieldName)};
                            end
                        end
                    end


                elseif isnumeric(iknot)
                    % Ensure iknot is within bounds for all fields in KnotDataStruct
                    maxIndex = max(structfun(@(field) numel(field), app.KnotDataStruct));
                    if iknot > maxIndex
                        fprintf('Warning in updateKnotDataStructWithUI(): iknot=%d exceeds the size of >0 fields. The field(s) will be resized\n', iknot);
                    end
                
                    for fieldNameCell = fieldnames(newStruct).'
                        fieldName = cell2mat(fieldNameCell);
                
                        % Check if the field exists in KnotDataStruct
                        if isfield(app.KnotDataStruct, fieldName)
                            % Check if it's a cell array field
                            if ismember(fieldName, app.KnotDataCellFields)
                                % Ensure the value is a cell array
                                app.KnotDataStruct.(fieldName){iknot} = newStruct.(fieldName){iknot};
                            else
                                % Assign the new value for non-cell array fields. Will resize if necessary
                                app.KnotDataStruct.(fieldName)(iknot) = newStruct.(fieldName)(iknot);
                            end
                        else
                            % Initialize the field if it does not exist
                            if ismember(fieldName, app.KnotDataCellFields)
                                % Initialize as a cell array
                                app.KnotDataStruct.(fieldName) = cell(1, maxIndex);
                                app.KnotDataStruct.(fieldName){iknot} = newStruct.(fieldName){iknot};
                            else
                                % Initialize as a regular array
                                app.KnotDataStruct.(fieldName) = zeros(1, maxIndex);
                                app.KnotDataStruct.(fieldName)(iknot) = newStruct.(fieldName)(iknot);
                            end
                            fprintf('Warning in updateKnotDataStructWithUI(): Field "%s" initialized and assigned a value at position %d\n', fieldName, iknot);
                        end
                    end
                else
                    error('Error in updateKnotDataStructWithUI(): "iknot" must be a valid index within the range of KnotDataStruct fields, or "all".');
                end

            else
                if ~exist('iknot', 'var')
                    iknot = str2num(app.KnotDropDown.Value);
                end

                % Read KnotData from UI
                if app.DeadCheckBox.Value; type = 'D'; else; type = 'G'; end % D = Dead, G = Green (alive)

                % Depending on type, some data have an alternative value, here we need to interpret this back to the KnotDataStruct.
                % Not the difference in type dependant/independant here vs in updateKnotUIFromKnotDataStruct().
                % 'type' independent:
                app.KnotDataStruct.Knot_type{iknot}     = type;
                app.KnotDataStruct.Azimuth(iknot)       = app.AzimuthEditField.Value;
                app.KnotDataStruct.Knot_start(iknot, :) = str2num(app.KnotStartStoreEditField.Value);
                app.KnotDataStruct.L1_a(iknot)          = app.L1aEditField.Value;
                app.KnotDataStruct.L1_b(iknot)          = app.L1bEditField.Value;
                app.KnotDataStruct.L4(iknot)            = app.L4EditField.Value;
                app.KnotDataStruct.L5(iknot)            = app.L5EditField.Value;
                % 'type' dependant:
                if strcmp(type, 'D')
                    % Only dead knots has 'D1' meaning if you are editing a
                    % dead knot, store that diameter data in 'D1'
                    app.KnotDataStruct.D1(iknot)        = app.DiameterEditField.Value;
                else
                    % All knots has 'Knot_Diam' meaning if you are editing
                    % a green knot, store that diameter data in 'Knot_Diam'
                    app.KnotDataStruct.Knot_Diam(iknot) = app.DiameterEditField.Value;
                end
            end

            % fprintf('Internal knot data updated\n')
            focus(app.CTRegistratorUIFigure)
        end

        function updateKnotUIFromKnotDataStruct(app)
            %% Creates or updates the Knot UI from app.KnotDataStruct
            %%% Which knot are we dealing with
            try
                iknot = app.KnotDataStruct.KNOT_NO(end);

                app.KnotadjustmentsPanel.Title = ['Knot adjustments (' num2str(iknot) ' knots)'];

                app.KnotDropDown.Items = cellstr(string(1:iknot));
                app.NextKnotButton.Enable = str2num(app.KnotDropDown.Value) < iknot;

                iknot = min(str2num(app.KnotDropDown.Value), iknot);
            catch % KNOT_NO is []
                error('There does not appear to be any Knot Data in the selected file!')
            end

            
            %%% Process each variable:
            % Knot_start
            try % For when app.KnotDataStruct.Knot_start is not initialized or non-indexable empty cell
                app.KnotStartStoreEditField.Value = sprintf('%d,  %d,  %d', app.KnotDataStruct.Knot_start(iknot, :));
            catch
                app.KnotStartStoreEditField.Value = '';
            end
    
            %%% The remaining variables:
            type = strcmp(app.KnotDataStruct.Knot_type{iknot}, 'D');

            % Depending on type, some data have missing values (NANs) which are represented by -1 in the UI.
            % 'type' independant:
            app.AzimuthEditField.Value      = app.KnotDataStruct.Azimuth(iknot);
            app.DeadCheckBox.Value          = type;

            %'type' dependant:
            if type % Dead
                app.L1aEditField.Value = app.KnotDataStruct.L1_a(iknot);
                app.L1bEditField.Value = app.KnotDataStruct.L1_b(iknot);
                app.L4EditField.Value = app.KnotDataStruct.L4(iknot);
                app.L5EditField.Value = app.KnotDataStruct.L5(iknot);
                app.DiameterEditField.Value = app.KnotDataStruct.D1(iknot);
            else 
                % For Green knots, some values are NAN meaning the are not measured for Green knots so let's create them using the app.
                % Values are no longer NAN if a matching has already been performed
                % L1 a
                if isnan(app.KnotDataStruct.L1_a(iknot))
                    app.L1aEditField.Value = app.KnotDataStruct.R1(iknot);
                else
                    app.L1aEditField.Value = app.KnotDataStruct.L1_a(iknot);
                end
                % L1 b
                if isnan(app.KnotDataStruct.L1_b(iknot))
                    app.L1bEditField.Value = app.KnotDataStruct.R1(iknot);
                else
                    app.L1bEditField.Value = app.KnotDataStruct.L1_b(iknot);
                end
                % L4
                if isnan(app.KnotDataStruct.L4(iknot))
                    app.L4EditField.Value = -1;
                else
                    app.L4EditField.Value = app.KnotDataStruct.L4(iknot);
                end
                % L5
                if isnan(app.KnotDataStruct.L5(iknot))
                    app.L5EditField.Value = -1;
                else
                    app.L5EditField.Value = app.KnotDataStruct.L5(iknot);
                end
                % D1
                if isnan(app.KnotDataStruct.D1(iknot))
                    app.DiameterEditField.Value = app.KnotDataStruct.Knot_Diam(iknot);
                else
                    app.DiameterEditField.Value = app.KnotDataStruct.D1(iknot);
                end
            end

            focus(app.CTRegistratorUIFigure)
        end

        function updateAzimuthEndView(app)
            %%
            if isempty(app.KnotStartStoreEditField.Value) || any(str2num(app.KnotStartStoreEditField.Value) < 10); return; end
            % Draw points along the z-direction to highlight the position
            % of the knot(s) with their currect azimuth angle which is to
            % be fine-tuned.
            app.PlotLamp.Color = [1 0 0];
            drawnow
            sf = 0.5; % Scanner setting: [mm/pixels]
            iknot = str2num(app.KnotDropDown.Value);

            Azimuth = app.AzimuthEditField.Value;
            L1a = app.L1aEditField.Value;
            L1b = app.L1bEditField.Value;
            D1 = app.DiameterEditField.Value;
            L4 = app.L4EditField.Value;
            L5 = app.L5EditField.Value;

            markedWV = app.dryVolume; % Marked Whorl Volume

            %%% Read whorlStart and create markings.
            whorlStart = str2num(app.KnotStartStoreEditField.Value);
            [ya,xa,za] = pol2cart(deg2rad(Azimuth),L1a/sf,L4/sf); % NOTE switch of [y,x,z] = ... such that X,Y below becomes correct x-y-directions relative to the markeWV (definitions "x, y" = "col, rows").
            [yb,xb,zb] = pol2cart(deg2rad(Azimuth),L1b/sf,L4/sf); % We'll correct the z-coordinate elsewhere, for now treat them as the same z-coordinate.

            markedWV(whorlStart(2)-1:whorlStart(2)+1,whorlStart(1)-1:whorlStart(1)+1, :) = max(markedWV(:));
            
            %%% Mark the points a and b similar to whorl start.
            [Xa,Ya,Za] = deal(whorlStart(1)+xa, whorlStart(2)+ya, whorlStart(3)-za); % NOTE the negative za due to orientation of log relative marking points
            [Xb,Yb,Zb] = deal(whorlStart(1)+xb, whorlStart(2)+yb, whorlStart(3)-zb); % NOTE the negative zb due to orientation of log relative marking points

            markedWV(round(Ya)-1:round(Ya)+1, round(Xa)-1:round(Xa)+1, :) = max(markedWV(:));
            markedWV(round(Yb)-1:round(Yb)+1, round(Xb)-1:round(Xb)+1, :) = max(markedWV(:));

            %%% Copy existing panel, delete it, create an identical one, plot on it, repeat next time, cry. This is because it doesn't seem to be a way to delete the sliceviewer without deleteing the entire UIPanel, so lets do that.
            % Copy existing sliceViewer and panel properties (and, if possible, use the same slice).
            % TODO: Should be able to replace all other settings, like contrast changes
            h = allchild(app.AzimuthEndViewPanel);
            if isempty(h)
                slice = round(Za+L5);
            else
                slice = h(3).Value;
                XLim = h(6).XLim;
                YLim = h(6).YLim;
                CLim = h(6).CLim;
            end

            position = app.AzimuthEndViewPanel.Position;
            title = app.AzimuthEndViewPanel.Title;

            % Delete and re-make
            delete(app.AzimuthEndViewPanel)
            app.AzimuthEndViewPanel = uipanel('Title',title,'Position',position,'Parent',app.KnotsTab);

            % Plot
            s = sliceViewer(markedWV, 'SliceNumber',slice,'Parent',app.AzimuthEndViewPanel);
            s.DisplayRange = [100 1500]; % Default

            % Replicate any existing zoom
            if exist('XLim','var')
                h = allchild(app.AzimuthEndViewPanel);
                h(6).XLim = XLim;
                h(6).YLim = YLim;
                h(6).CLim = CLim;
            end


            ConfigureUI(app);
            app.PlotLamp.Color = [0 1 0];
            focus(app.CTRegistratorUIFigure)
        end
        
        function updateKnotCrossSectionView(app)
            %%
            whorlStart = str2num(app.KnotStartStoreEditField.Value); % x, y, slice
            if any(whorlStart < 10); return; end

            app.PlotLamp.Color = [1 0 0];
            drawnow
            sf = 0.5; % scale factor [mm/pixels]
            iknot = str2num(app.KnotDropDown.Value);

            Azimuth = app.AzimuthEditField.Value;
            L1a = app.L1aEditField.Value;
            L1b = app.L1bEditField.Value;
            D1  = app.DiameterEditField.Value;
            L4  = app.L4EditField.Value;
            L5  = app.KnotDataStruct.('L5')(iknot);

            % "Marked Cross Section"
            markedCS = app.dryVolume;

            %%% Mark whorlStart as a 3x3x3 dot in the markedCD volume
            markedCS(whorlStart(2)-1:whorlStart(2)+1,whorlStart(1)-1:whorlStart(1)+1,whorlStart(3)-1:whorlStart(3)+1) = max(markedCS(:)); % row, col, slice
            
            %%% Define the points a and b in poolar coordinates
            % NOTE switch of y and y in [y,x,z] such that X,Y,Z below becomes correct x-y-directions relative to the marked volume (markedCS).
            % The z-direction needs to be fliped, hence the -za and -zb in the rows below
            % za and zb will be the same here. Their z-direction ("height") difference will be added below
            [ya,xa,za] = pol2cart(deg2rad(Azimuth),L1a/sf,L4/sf);
            [yb,xb,zb] = pol2cart(deg2rad(Azimuth),L1b/sf,L4/sf);

            [Xa,Ya,Za] = deal(whorlStart(1)+xa, whorlStart(2)+ya, whorlStart(3)-za);
            [Xb,Yb,Zb] = deal(whorlStart(1)+xb, whorlStart(2)+yb, whorlStart(3)-zb);

            % Apply the L5 measurement
            Zb = Zb + L5/sf;

            %%% Mark the points a and b
            extraBrightness = 50;
            markedCS(round(Ya)-1:round(Ya)+1,round(Xa)-1:round(Xa)+1,round(Za)-1:round(Za)+1) = max(markedCS(:)) + extraBrightness;
            markedCS(round(Yb-1):round(Yb+1),round(Xb-1):round(Xb+1),round(Zb-1):round(Zb+1)) = max(markedCS(:)) + extraBrightness;

            %%% Rotatatations
            % Flip markedCS such that it's "standing"
            % markedCS = flip(permute(markedCS, [3 2 1]), 3);
            % 
            % % Rotate it according to Azimuth such that one slice shows a cross section view of the current knot.
            % markedCS = imrotate3(markedCS,-Azimuth,[0 1 0]);

            % Rotate such that the current knot lies in the Y (rows) direction
            markedCS = imrotate3(markedCS,-Azimuth,[0 0 1]);
            markedCS = permute(markedCS, [3 2 1]);
            
            %%% Copy existing panel, delete it, create an identical one, plot on it, repeat next time, cry. This is because it doesn't seem to be a way to delete the sliceviewer without deleteing the entire UIPanel, so lets do that.
            % Copy existing sliceViewer and panel properties (and, if possible, use the same slice).
            % TODO: Should be able to replace all other settings, like contrast changes
            h = allchild(app.KnotCrossSectionViewPanel);
            if isempty(h)
                %%% This doesn't work when imrotate3 above does NOT use 'crop' setting
                % % Using math, calculate the rotation of the points to be used for calculating an appropriet starting slice below.
                % center = round(size(app.dryVolume,[2 1])/2)';
                % theta = deg2rad(Azimuth);
                % R = [cos(theta) -sin(theta); sin(theta) cos(theta)];
                % XaRotated = round(R*([Xa;Ya] - center) + center);
                % slice = XaRotated(1);

            else
                % Use existing settings
                % slice = h(3).Value;
                XLim = h(6).XLim;
                YLim = h(6).YLim;
                CLim = h(6).CLim;
            end

            position = app.KnotCrossSectionViewPanel.Position;
            title = app.KnotCrossSectionViewPanel.Title;

            % Delete existing panel, replace it, then plot the sliceViewer
            delete(app.KnotCrossSectionViewPanel)
            app.KnotCrossSectionViewPanel = uipanel('Title',title,'Position',position,'Parent',app.KnotsTab);

            % Plot with optional crop
            if app.CropKCSviewCheckBox.Value
                if strcmp(app.KnotDataStruct.Knot_type(iknot),'G')
                    topCrop = 75;
                else
                    topCrop = max(1, size(app.dryVolume,3)-Za-75);
                end
                buttCrop = whorlStart(3)+75;
                markedCS([1:topCrop buttCrop:end],:,:) = [];
            end

            % Find the markings and determine which slice to view
            [~,c,~] = ind2sub(size(markedCS),find(markedCS > max(markedCS(:)) - extraBrightness));
            slice = round(mean(c));

            s = sliceViewer(markedCS, 'SliceNumber', slice, 'SliceDirection', 'x', 'Parent', app.KnotCrossSectionViewPanel);
            s.DisplayRange = [100 1500]; % Default
            
            % Replicate any existing zoom
            if exist('XLim','var')
                h = allchild(app.KnotCrossSectionViewPanel);
                h(6).XLim = XLim;
                h(6).YLim = YLim;
                h(6).CLim = CLim;
            end

            app.PlotLamp.Color = [0 1 0];
            ConfigureUI(app)
            focus(app.CTRegistratorUIFigure)
        end
        
        function SaveMatching(app, overwrite)
            %%
            arguments
                app
                overwrite logical = false
            end
            fprintf('Starting SaveMatching...')

            % Check if the user is viewing different slices, which might mean that the user thinks they have aligned the bodies but forgot to press the 'app.TranslationAlign12Button' (or ctrl+1) button.
            adjustSliceDifference(app)

            %%% Make disks to be the same size
            % Modifications are truncating/padding at the bottom and right in the End view. It is not impossible for this to crop the dry volume slighlty...
            % Rows
            if size(app.dryVolume,1) > size(app.wetVolume,1)
                app.dryVolume = app.dryVolume(1:size(app.wetVolume,1),:,:);
            elseif size(app.dryVolume,1) < size(app.wetVolume,1)
                app.dryVolume = cat(1, app.dryVolume, zeros(size(app.wetVolume,1)-size(app.dryVolume,1), size(app.dryVolume,2), size(app.dryVolume,3)));
            end

            % Columns
            if size(app.dryVolume,2) > size(app.wetVolume,2)
                app.dryVolume = app.dryVolume(:,1:size(app.wetVolume,2),:);
            elseif size(app.dryVolume,2) < size(app.wetVolume,2)
                app.dryVolume = cat(2, app.dryVolume, zeros(size(app.dryVolume,1), size(app.wetVolume,2)-size(app.dryVolume,2), size(app.dryVolume,3)));
            end

            % Slices
            if size(app.dryVolume,3) > size(app.wetVolume,3)
                app.dryVolume = app.dryVolume(:,:,1:size(app.wetVolume,3));
            elseif size(app.dryVolume,3) < size(app.wetVolume,3)
                app.dryVolume = cat(3, app.dryVolume, zeros(size(app.dryVolume,1), size(app.dryVolume,2), size(app.wetVolume,3)-size(app.dryVolume,3)));
            end

            % Save location. If the user saves the disk using the app, the user has performed the matching, 
            % or reviewd the match carefully, meaning it's suitable to save it as manually matched.
            DryDiskFile = GetDiskFile(app, 'Matched manually');

            % Overwrite existing files?
            if isempty(DryDiskFile)
                write_path = fullfile(app.SelectDataFolderButton.Text, 'Disks', app.SelectedTreeDropDown.Value, 'Prep', 'Matched manually', [app.SelectedDryFileDropDown.Value '.nrrd']);
            else
                if exist(fullfile(DryDiskFile.folder, DryDiskFile.name), 'file')
                    if ~overwrite
                        fig = uifigure;
                        selection = uiconfirm(fig,'Overwrite exsisting file?','File already exists','Icon','warning');
                        delete(fig);
                        if strcmp(selection, 'Cancel'); fprintf('aborted\n'); return; end
                    end
                    write_path = fullfile(DryDiskFile.folder, DryDiskFile.name);
                end
            end

            % TODO: If KnotDataStruct has not been modified for any knots, 
            % ask user to confirm calling SaveAllKnotsButtonPressed, otherwise, don't save any knot header to save time
            screenSize = get(groot, 'ScreenSize');
            waitFig = uifigure('Name', 'Please Wait', 'Position', [round(screenSize(3)/2) round(screenSize(4)/2) 250 80], 'Color', [0.94 0.94 0.94], 'WindowStyle', 'modal');
            uilabel(waitFig, 'Text', 'Writing Matched Data... (~15s)', 'Position', [20 30 210 20], 'HorizontalAlignment', 'center');
            drawnow

            %%% Save the data to the NRRD file:
            % The Python script copies the twin file from the 'Dry' folder
            % to the 'DryDiskFile' path such that e.g. scanner settings
            % info in the header.
            % Prints "Data written successfully to <path>".

            % The dryVolume data needs to be passed to Python by a temp file, 
            % let's use HDF5 to ensure size, shape, type of the data to be correctly captured by Python next.
            [filepath, ~, ~] = fileparts(write_path);
            full_filename = fullfile(filepath, 'temp.h5');
            dataset = '/data';
            data = app.dryVolume;
            
            % Create HDF5 file and dataset
            h5create(full_filename, dataset, size(data), 'Datatype', class(app.dryVolume));
            
            % Write data to the HDF5 file
            h5write(full_filename, dataset, data);

            % print("Usage: python WAI-KnotCTnrrdWrite.py <target_path> <data_matrix>")
            python_command = sprintf('"%s" "%s" "%s"', app.python_path, app.WAIKnotCTnrrdWrite, write_path);
    
            [py_status, py_output] = system(python_command);
            if py_status == 1
                fprintf("\n\tError writing 'Matched manually'-disk to path: %s\n\t\t...with output: %s\n", write_path, py_output);
                app.SavematchedwhorlButton.BackgroundColor = [1 0 0];
                beep
            else
                if length(py_output) > 100; py_output(98:100) = '.'; end
                fprintf("\n\tSuccessfully wrote 'Matched manually'-disk to path: %s\n\t\t...with output:\n\t\t%.100s\n", write_path, py_output);
                % fprintf('%s\n', jsonencode(jsondecode(py_output), 'PrettyPrint', true));
                app.SavematchedwhorlButton.BackgroundColor = [0.5961 0.9843 0.5961]; % Pale green
            end

            % Delete temp file
            delete(full_filename); 

            delete(waitFig)
            app.SavematchedwhorlButton.BackgroundColor = [0.5961 0.9843 0.5961]; % Pale green
            focus(app.CTRegistratorUIFigure)
        end

        function SaveAllKnots(app, overwrite)
            %%
            arguments
                app
                overwrite logical = false
            end

            fprintf('Starting SaveAllKnots...')

            defaultOption = 'Matched manually';
            
            % Used to get the folder path.
            DryDiskFile = GetDiskFile(app, defaultOption);

            if isempty(DryDiskFile)
                fig = uifigure;
                selection = uiconfirm(fig, ...
                    "Save matched whorl first.","No manually matched file.", ...
                    "Icon","warning");
                delete(fig)
                fprintf('aborted\n')
                return
            end

            app.PlotLamp.Color = [1 0 0];
            drawnow

            % Save Knot Data to which files? 
            options = dir(fullfile(DryDiskFile.folder, '..'));
            options(logical(~strcmp({options.name},'Wet').*~strcmp({options.name},'Matched manually'))) = []; % Beautiful implementation...

            % TODO: For now, always write to 'Matched manually' and 'Wet'.
            indx = 1:length({options.name});
            % defaultIndex = find(strcmp({options.name}, defaultOption));
            % 
            % [indx, tf] = listdlg('ListString', {options.name}, 'InitialValue', defaultIndex, 'PromptString', 'Select 1 or more files to save the Knot Data to.', 'Name', 'File Selection');
            % if ~tf; return; end

            % All files needs to exist, otherwise the user might be doing something incorrect.
            for i = indx
                fileData = GetDiskFile(app, options(i).name);
                filePath = fullfile(fileData.folder, fileData.name);
            
                if ~exist(filePath, 'file')
                    fig = uifigure;
                    selection = uiconfirm(fig, ...
                        "Could not find both 'Wet' and 'Matched manually' files to write Knot Data to.","Missing file.", ...
                        "Icon","warning");
                    delete(fig)
                    fprintf('exiting\n')
                    error('\tTrying to write Knot Data to file that does not exist:\n\t\t%s', filePath);
                end
            end

            % Overwrite existing files?
            if ~overwrite
                fig = uifigure;
                selection = uiconfirm(fig, 'Overwrite Knot Data in all selected files?', 'Confirm Overwrite', 'Icon', 'warning');
                delete(fig);
                if strcmp(selection, 'Cancel'); fprintf('aborted\n'); return; end
            end
            
            % Write Knot Data to each selected file
            screenSize = get(groot, 'ScreenSize');
            waitFig = uifigure('Name', 'Please Wait', 'Position', [round(screenSize(3)/2) round(screenSize(4)/2) 250 80], 'Color', [0.94 0.94 0.94], 'WindowStyle', 'modal');
            uilabel(waitFig, 'Text', 'Writing Knot Data... (~15s per file)', 'Position', [20 30 210 20], 'HorizontalAlignment', 'center');
            drawnow
            
            %%% Saves the header to each NRRD file using 'nrrdHeaderReadWrite.py':
            action = 'edit';
            json_str = PythonFormattedFieldNamesOfKnotDataStructOrStr(app);
            json_data_str = jsonencode(json_str);

            % jsonecode does not correctly format the string if the data is only 1 long: "a":42 instead of the required "a":[42].
            if app.KnotDataStruct.KNOT_NO(end) == 1
                % Regular expression pattern: anything between a ":" and a "," where "[]" are not allowed (arrays).
                pattern_general = '":([^,\[\]]*)[,}]';
                % Replacement pattern
                replacement_general = '":[$1],';
                % Applying regex replacement for general case
                json_data_str = regexprep(json_data_str, pattern_general, replacement_general);
            
                % Specific pattern for 'Knot start' field with a single set of coordinates
                pattern_knotStart = '\\"Knot start\\":\[(\d+),(\d+),(\d+)\]';
                replacement_knotStart = '\\"Knot start\\":[[$1,$2,$3]]';
                % Applying regex replacement for 'Knot start'
                json_data_str = regexprep(json_data_str, pattern_knotStart, replacement_knotStart);
            
                % Specific pattern for 'Knot start' field with empty coordinates
                pattern_knotStart_empty = '\\"Knot start\\":\[\]';
                replacement_knotStart_empty = '\\"Knot start\\":[[]]';
                % Applying regex replacement for empty 'Knot start'
                json_data_str = regexprep(json_data_str, pattern_knotStart_empty, replacement_knotStart_empty);
            end

            for i = indx
                fileData = GetDiskFile(app, options(i).name);
                write_path = fullfile(fileData.folder, fileData.name);

                python_command = sprintf('"%s" "%s" "%s" "%s" %s', app.python_path, app.nrrdHeaderReadWritePyPath, write_path, action, json_data_str);
        
                [py_status, py_output] = system(python_command);
                if py_status == 1
                    fprintf('\n\tError writing Knot Data for: %s\n\t\t...to path: %s\n\t\t\t...with output: %s\n', options(i).name, write_path, py_output);
                    app.SaveallknotsButton.BackgroundColor = [1 0 0];
                    beep
                else
                    fprintf('\n\tSuccessfully wrote Knot data for: %s\n\t\t...to path: %s\n\t\t\t...with output: %s\n', options(i).name, write_path, py_output);
                    app.SaveallknotsButton.BackgroundColor = [0.5961 0.9843 0.5961]; % Pale green
                end
            end

            delete(waitFig)

            app.PlotLamp.Color = [0 1 0];
            drawnow
            focus(app.CTRegistratorUIFigure)
        end
        
        function TranslateWetTopToDryTopIn3D(app, x_trans, y_trans, slice_trans)
            %%
            if app.LockOriginsButton.Value; beep; return; end

            %%% Determine the translation vector
            if nargin < 4  % If less than 4 arguments, calculate the translation vector
                % Get marked feature coordinates (buttons: 1 dry, 2 wet)
                dry_feature = [str2num(app.DryTopPointStoreEditField.Value) str2num(app.DryTopPointSliceEditField.Value)];
                wet_feature = [str2num(app.WetTopPointStoreEditField.Value) str2num(app.WetTopPointSliceEditField.Value)];
                if ~exist("dry_feature","var") || ~exist("wet_feature","var"); beep; return; end

                translation_vector = wet_feature - dry_feature;
            else
                translation_vector = [x_trans, y_trans, slice_trans];
            end
            
            % UI
            app.SaveallknotsButton.BackgroundColor = [0.96 0.96 0.96];
            app.SavematchedwhorlButton.BackgroundColor = [0.96 0.96 0.96];
            app.PlotLamp.Color = [1 0 0];
            drawnow
            
            %%% Perform the translation
            % Apply the translation to the dry volume
            % Create a translation affine transformation matrix
            tformTranslation = affine3d([1 0 0 0; 0 1 0 0; 0 0 1 0; translation_vector 1]);
            
            % Apply the transformation using imwarp. Since we are only translating by full pixel steps, we use 'interp' 'nearest'.
            if translation_vector == round(translation_vector) % If all integers
                interpolation_method = 'linear';
            else
                interpolation_method = 'cubic';
            end
            [translated_dry_volume, RB] = imwarp(app.dryVolume, tformTranslation, 'interp', interpolation_method, 'OutputView', imref3d(size(app.dryVolume)));
            
            app.dryVolume = translated_dry_volume;

            % fprintf("Translated by\n\tx_diff = %.1f\n\ty_diff = %.1f\n\ts_diff = %.1f\n" ,translation_vector(1), translation_vector(2), translation_vector(3))

            %%% UI stuff
            if nargin < 4
                app.DryTopPointStoreEditField.Value = app.WetTopPointStoreEditField.Value;
                app.DryTopPointSliceEditField.Value = app.WetTopPointSliceEditField.Value;
                app.EndDrySlider.Value = round(str2num(app.WetTopPointSliceEditField.Value));
                app.EndWetSlider.Value = round(str2num(app.WetTopPointSliceEditField.Value));

                % app.EndDrySlider.Value = round(app.EndDrySlider.Value + translation_vector(3));
                % % app.EndWetSlider.Value = app.EndDrySlider.Value;
            end

            updateView(app)            
        end
        
        function AlignWetButtWithDryButtGivenWetTopAndDryTop(app, angleX, angleY)
            %%
            if app.LockPointsButton.Value; beep; return; end

            %%% Check requirements           
            % Center marking(s), preferably at the top end of the log
            c1 = [str2num(app.WetTopPointStoreEditField.Value) str2num(app.WetTopPointSliceEditField.Value)];
            c2 = [str2num(app.DryTopPointStoreEditField.Value) str2num(app.DryTopPointSliceEditField.Value)];
            pointOfRotation = mean([c1;c2]);

            % centre is nan if both c1 and c2 are empty.
            if isnan(pointOfRotation); beep; return; end
            
            % UI
            app.SaveallknotsButton.BackgroundColor = [0.96 0.96 0.96];
            app.SavematchedwhorlButton.BackgroundColor = [0.96 0.96 0.96];
            app.PlotLamp.Color = [1 0 0];
            drawnow
            
            %%% If angleX and angleY are both not given as inputs - calculate them
            if nargin < 3
                % Mark a feature (buttons: 3 <- dry, 4 <- wet) (at the butt end of the log)
                dry_feature = [str2num(app.WetButtPointStoreEditField.Value) str2num(app.WetButtPointSliceEditField.Value)];
                wet_feature = [str2num(app.DryButtPointStoreEditField.Value) str2num(app.DryButtPointSliceEditField.Value)];
                
                if ~exist("dry_feature","var") || ~exist("wet_feature","var"); beep; return; end
    
                % Vectors from the center to the features
                dry_vector = dry_feature - pointOfRotation;
                wet_vector = wet_feature - pointOfRotation;
    
                % Calculate rotation angles
                % For rotation around the X-axis, project onto the YZ plane (set the x-component to 0)
                dry_vector_YZ = [0, dry_vector(2), dry_vector(3)];
                wet_vector_YZ = [0, wet_vector(2), wet_vector(3)];
                angleX = atan2d(norm(cross(dry_vector_YZ, wet_vector_YZ)), dot(dry_vector_YZ, wet_vector_YZ));
    
                % For rotation around the Y-axis, project onto the XZ plane (set the y-component to 0)
                dry_vector_XZ = [dry_vector(1), 0, dry_vector(3)];
                wet_vector_XZ = [wet_vector(1), 0, wet_vector(3)];
                angleY = atan2d(norm(cross(dry_vector_XZ, wet_vector_XZ)), dot(dry_vector_XZ, wet_vector_XZ));
    
                % Calculate the cross product to determine the direction of rotation
                cross_product_X = cross(dry_vector_YZ, wet_vector_YZ);
                cross_product_Y = cross(dry_vector_XZ, wet_vector_XZ);
                
                % Determine the direction of the rotation.
                % If cross_product in X (1) is positive, wet_vector is counterclockwise from dry_vector, and the angle should be negative.
                if cross_product_X(1) > 0
                    angleX = -angleX;
                end
                
                if cross_product_Y(2) > 0
                    angleY = -angleY;
                end
            end

            %%% Perform the rotation
            % Create rotation matrices around the X-axis and Y-axis
            rotationMatrixX = makehgtform('xrotate', deg2rad(angleX));
            rotationMatrixY = makehgtform('yrotate', deg2rad(angleY));
            
            % Combine the rotation matrices
            combinedRotationMatrix = rotationMatrixX * rotationMatrixY;
            
            % Translate the volume origin to the point of rotation
            translationMatrixToOrigin = makehgtform('translate', -pointOfRotation);
            
            % Combine the translation to the origin with the rotations
            affineMatrix = translationMatrixToOrigin * combinedRotationMatrix;
            
            % Translate back to the original center
            translationMatrixBackToCenter = makehgtform('translate', pointOfRotation);

            % Combine in correct order
            finalAffineMatrix = affineMatrix*translationMatrixBackToCenter;
            
            % Convert to affine3d object
            finalAffine3D = affine3d(finalAffineMatrix');
            
            % Apply the transformation
            [rotated_dry_volume, RB] = imwarp(app.dryVolume, finalAffine3D, 'Interpolation', 'cubic', 'OutputView', imref3d(size(app.dryVolume)));
            
            app.dryVolume = rotated_dry_volume;

            % fprintf("Rotated by \n\tangleX = %.1f \n\tangleY = %.1f\n", angleX, angleY)
            
            %%% UI stuff
            app.DryButtPointSliceEditField.Value = app.WetButtPointSliceEditField.Value;
            app.DryButtPointStoreEditField.Value = app.WetButtPointStoreEditField.Value;
            app.LockPointsButton.Enable = 1;

            maskWhorl(app) % The use of cubic can introduce negative values, which are removed in this masking.
            updateView(app)
        end
        
        function RotateToAlignWetButtWithDryButtInEndViewIn2D(app, angleZ)
            if ~app.RotateMButton.Enable; beep; return; end

            app.SaveallknotsButton.BackgroundColor = [0.96 0.96 0.96];
            app.SavematchedwhorlButton.BackgroundColor = [0.96 0.96 0.96];

            %%% Get necessary data
            % Center markings
            c1 = str2num(app.WetTopPointStoreEditField.Value);  % Wet center point
            c2 = str2num(app.DryTopPointStoreEditField.Value);  % Dry center point
            center = mean([c1;c2]);  % Compute the average center
            
            if ~exist("center","var"); beep; return; end % center is always required
            
            app.PlotLamp.Color = [1,0,0];
            drawnow

            if nargin < 2
                % Mark a feature (buttons: 1 dry, 2 wet)
                dry_feature = str2num(app.DryButtPointStoreEditField.Value);
                wet_feature = str2num(app.WetButtPointStoreEditField.Value);
        
                if ~exist("dry_feature","var") || ~exist("wet_feature","var"); beep; return; end
        
                % Calculate the vectors from the center to the features
                dry_vector = dry_feature - center;
                wet_vector = wet_feature - center;
                
                % Normalize the vectors
                dry_vector = dry_vector / norm(dry_vector);
                wet_vector = wet_vector / norm(wet_vector);
                
                %%% Calculate the angle of rotation
                % Angle of rotation in degrees using the arccosine of the dot product
                angleZ = acosd(dot(dry_vector, wet_vector)); % [0 180]
                
                % Compute the cross product of the vectors
                cross_product = cross([dry_vector, 0], [wet_vector, 0]);
                
                % Determine the direction of the rotation.
                if cross_product(3) > 0
                    angleZ = -angleZ;
                end
            end
        
            %%% Perform the rotation using affine3d and imwarp
            % Define the reference object for the default coordinate system used by imwarp
            Rdefault = imref3d(size(app.dryVolume));

            % Find the center of the volume in the world coordinates
            tX = mean(Rdefault.XWorldLimits);
            tY = mean(Rdefault.YWorldLimits);
            tZ = mean(Rdefault.ZWorldLimits);

            % Define the translation that moves the center of the volume to the origin
            tTranslationToCenterAtOrigin = [1 0 0 0; 0 1 0 0; 0 0 1 0; -tX -tY -tZ 1];

            % Define the rotation matrix around the Z-axis
            tRotation = [cosd(angleZ) -sind(angleZ) 0 0; sind(angleZ) cosd(angleZ) 0 0; 0 0 1 0; 0 0 0 1];

            % Define the translation that moves the origin back to the center of the volume
            tTranslationBackToOriginalCenter = [1 0 0 0; 0 1 0 0; 0 0 1 0; tX tY tZ 1];

            % Combine the transformations to form a centered rotation
            tformCenteredRotation = affine3d(tTranslationToCenterAtOrigin * tRotation * tTranslationBackToOriginalCenter);

            % Apply the transformation
            [rotated_Volume, RB] = imwarp(app.dryVolume, tformCenteredRotation, 'interp', 'cubic', 'OutputView', Rdefault);

            % Replace the original volume with the rotated volume
            app.dryVolume = rotated_Volume;

            % fprintf("Rotated by \n\tangleZ = %.1f\n", angleZ)

            maskWhorl(app) % The use of cubic can introduce negative values, which are removed in this masking.
            updateView(app)
        end
        
    end

    % Callbacks that handle component events
    methods (Access = private)

        % Code that executes after component creation
        function startupFcn(app)
            % Create PMs (pointer manager) to track mouse location for log/whorl in End view
            pmEnd.enterFcn = [];
            pmEnd.exitFcn  = @(~,~) set(app.CursorEditField, 'Value', '');
            pmEnd.traverseFcn = @(~,~) set(app.CursorEditField, 'Value', sprintf('%.0f,  %.0f', app.UIAxesEnd.CurrentPoint(1,1:2)-[strcmp(app.displayMode,'montage')*(app.UIAxesEnd.CurrentPoint(1,1)>size(app.wetVolume,2))*size(app.wetVolume,2) 0]));
            iptSetPointerBehavior(app.UIAxesEnd, pmEnd)
            iptPointerManager(app.CTRegistratorUIFigure,'enable');
            set(app.CTRegistratorUIFigure,'WindowButtonMotionFcn',@(~,~) []) %dummy fcn so that currentpoint is continually updated

            drawnow; % Apparently this needs calling before maximized.
            app.CTRegistratorUIFigure.WindowState = 'maximized';

            disp('CT Registrator started successfully.')
            focus(app.CTRegistratorUIFigure)
        end

        % Button pushed function: SelectDataFolderButton
        function SelectDataFolderButtonPushed(app, event)
            if strcmp(getenv('username'),'Linus')
                LocalWorkingFolder = uigetdir(fullfile('E:', 'LocalWorkingFolder', 'WAI-knotCT_OlofB', 'Pine', 'STAND3-5'), 'Select STAND folder');
            else
                LocalWorkingFolder = uigetdir(fullfile('E:', 'CT Registrator'),'Select STAND folder');
            end
            if isnumeric(LocalWorkingFolder); beep; return; end

            app.SelectDataFolderButton.Text = LocalWorkingFolder;
            treeFolders = dir([LocalWorkingFolder '\Disks\Tree*']);

            app.SelectedTreeDropDown.Enable = 1;
            app.TreeDropDownLabel.Enable = 1;

            app.SelectedTreeDropDown.Items = {treeFolders.name}; % Sets .Value to first item without calling ValueChanged()
            if isempty(app.SelectedTreeDropDown.Items)
                app.delete
                error('Error in SelectDataFolderButtonPushed(): Empty or unsupported datastructure!');
            end

            if isempty(app.SelectedWetFileDropDown.Value)
                SelectedTreeDropDownValueChanged(app, struct('Value',app.SelectedTreeDropDown.Value));
            end
            
            disp('Folder structure loaded successfully.')

            % If not on Linus' machine, find Python and the nrrd script:
            if ~strcmp(getenv('username'), 'Linus')
                % nrrdHeaderReadWrite and WAIKnotCTnrrdWrite file writer (python based)
                pyscriptpath = uigetdir(fullfile('E:', 'CT Registrator'), "Select the folder containing the 'nrrdHeaderReadWrite.py' and 'WAI-KnotCTnrrdWrite.py' scripts");
                if isequal(pyscriptpath, 0); msgbox("The Python script is required for writing files and everything regarding Knot Data!"); return; end
                pyscriptfile = 'nrrdHeaderReadWrite.py';
                writefile = 'WAI-KnotCTnrrdWrite.py';
                app.nrrdHeaderReadWritePyPath = fullfile(pyscriptpath, pyscriptfile);
                app.WAIKnotCTnrrdWrite = fullfile(pyscriptpath, writefile);

                % Python
                pypath = uigetdir(fullfile('C:', 'Users', 'olof-local', 'AppData', 'Local', 'Programs', 'Python', 'Python312', 'python.exe'), "Select the folder containing 'python.exe'");
                if isequal(pypath, 0); msgbox("Python is required for writing files and everything regarding Knot Data!"); return; end
                pyfile = 'python.exe';
                app.python_path = fullfile(pypath, pyfile);
            end
            disp('Python.exe and nrrdHeaderReadWrite.py plausible.')

            focus(app.CTRegistratorUIFigure)
        end

        % Value changed function: SelectedTreeDropDown
        function SelectedTreeDropDownValueChanged(app, event)
            tree = event.Value;

            %%% Wet files
            wetFiles = dir([app.SelectDataFolderButton.Text '\Disks\' tree '\Prep\Wet']);
            wetFiles(1:2) = [];

            % Names can appear unsorted, I don't know why, so let's sort them
            wetWhorlNum = cellfun(@(x)sscanf(x,'Green Disk_%*d.%d.nrrd'), {wetFiles.name});
            [~,Sidx] = sort(wetWhorlNum);
            [~,sortedWetFiles,~] = fileparts({wetFiles(Sidx).name});

            app.SelectedWetFileDropDown.Items = sortedWetFiles;

            app.SelectedWetFileDropDown.Enable = 1;
            app.WetLabel.Enable = 1;

            %%% Dry files
            % First try the automatically registrated files, if they exist.
            dryFiles = dir([app.SelectDataFolderButton.Text '\Disks\' tree '\Prep\Matched automatic\Matched*']);
            
            if isempty(dryFiles)
                dryFiles = dir([app.SelectDataFolderButton.Text '\Disks\' tree '\Prep\Dry']);
                dryFiles(1:2) = [];
            end

            % Names can appear unsorted, I don't know why, so let's sort them
            dryWhorlNum = cellfun(@(y) sscanf(y,'%*d.%d'), cellfun(@(x) x(regexp(x,'[^a-zA-Z]')),{dryFiles.name},'UniformOutput',false)); % A bit complex Since file names can be in their originals or autmatically-/manually matched versions.
            [~,Sidx] = sort(dryWhorlNum);
            [~,sortedDryFiles,~] = fileparts({dryFiles(Sidx).name});

            app.SelectedDryFileDropDown.Items = sortedDryFiles;

            app.SelectedDryFileDropDown.Enable = 1;
            app.DryLabel.Enable = 1;

            %%% Continute
            app.LoadDataButton.Enable = 1;
            focus(app.CTRegistratorUIFigure)
        end

        % Value changed function: SelectedWetFileDropDown
        function SelectedWetFileDropDownValueChanged(app, event)
            try
                app.SelectedDryFileDropDown.Value = app.SelectedDryFileDropDown.Items( mod(find(strcmp(app.SelectedDryFileDropDown.Items,[app.SelectedDryFileDropDown.Value(regexp(app.SelectedDryFileDropDown.Value,'[^0-9.]')) event.Value(12:end)])), length(app.SelectedDryFileDropDown.Items)+1) );
            catch
                error("Could not find corresponding Dry file.")
            end
            focus(app.CTRegistratorUIFigure)
        end

        % Button pushed function: LoadDataButton
        function LoadDataButtonPushed(app, event)
            loadData(app)
        end

        % Button pushed function: XpButton
        function XpButtonPushed(app, event)
            if ~app.XpButton.Enable; return; end
            TranslateWetTopToDryTopIn3D(app, app.StepSize.Value, 0, 0)
        end

        % Button pushed function: XmButton
        function XmButtonPushed(app, event)
            if ~app.XmButton.Enable; return; end
            TranslateWetTopToDryTopIn3D(app,-app.StepSize.Value, 0, 0)
        end

        % Button pushed function: YpButton
        function YpButtonPushed(app, event)
            if ~app.YpButton.Enable; return; end
            TranslateWetTopToDryTopIn3D(app, 0, app.StepSize.Value, 0)
        end

        % Button pushed function: YmButton
        function YmButtonPushed(app, event)
            if ~app.YmButton.Enable; return; end
            TranslateWetTopToDryTopIn3D(app, 0,-app.StepSize.Value, 0)
        end

        % Button pushed function: ZpButton
        function ZpButtonPushed(app, event)
            if ~app.ZpButton.Enable; return; end
            TranslateWetTopToDryTopIn3D(app, 0, 0, app.StepSize.Value)
        end

        % Button pushed function: ZmButton
        function ZmButtonPushed(app, event)
            if ~app.ZmButton.Enable; return; end
            TranslateWetTopToDryTopIn3D(app, 0, 0,-app.StepSize.Value)
        end

        % Button pushed function: RotatePButton
        function RotatePButtonPushed(app, event)
            if ~app.RotatePButton.Enable; return; end
            RotateToAlignWetButtWithDryButtInEndViewIn2D(app, app.AngleSize.Value)
        end

        % Button pushed function: RotateMButton
        function RotateMButtonPushed(app, event)
            if ~app.RotateMButton.Enable; return; end
            RotateToAlignWetButtWithDryButtInEndViewIn2D(app,-app.AngleSize.Value)
        end

        % Key press function: CTRegistratorUIFigure
        function CTRegistratorUIFigureWindowButtonDown(app, event)
            if isequal(event.EventName,'WindowMousePress'); return; end
            if isempty(app.dryVolume); return; end

            % TODO: Make buttons the ones that handles the modifier 
            % somehow, such that the user can e.g. hold Alt and use mouse 
            % to click a button for the Alt effect to take place. Unclear 
            % how holding a button works.

            key = event.Key;
            modifier = event.Modifier;

            if ~isempty(modifier)
                if strcmp(modifier,'shift') % Opposite direction to the default (not-shift) key press.
                    switch key
                        case 'r'
                            app.RotatePButtonPushed(app)
                        case 'z'
                            app.ZmButtonPushed(app)
                        case 'q'
                            app.YawMButtonPushed(app)
                        case 'e'
                            app.PitchMButtonPushed(app)
                    end

                elseif strcmp(modifier,'alt') % Perform the action using 1/4th the magnitude, or take a medium sized slice step in the current view
                    tempstep = app.StepSize.Value;
                    tempangle = app.AngleSize.Value;
                    app.StepSize.Value = app.StepSize.Value/4;
                    app.AngleSize.Value = app.AngleSize.Value/4;
                    switch key
                        case 'd'
                            app.XpButtonPushed(app)
                        case 'a'
                            app.XmButtonPushed(app)
                        case 'w'
                            app.YmButtonPushed(app)
                        case 's'
                            app.YpButtonPushed(app)
                        case 'r'
                            app.RotateMButtonPushed(app)
                        case 'z'
                            app.ZpButtonPushed(app)
                        case 'q'
                            app.YawPButtonPushed(app)
                        case 'e'
                            app.PitchPButtonPushed(app) % Pitch
                        case 'rightarrow'
                            app.sliceStep = 10;
                            EndDrySliderPButtonPushed(app)
                            app.sliceStep = 1;
                        case 'leftarrow'
                            app.sliceStep = 10;
                            EndDrySliderMButtonPushed(app)
                            app.sliceStep = 1;
                    end
                    app.StepSize.Value = tempstep;
                    app.AngleSize.Value = tempangle;

                elseif strcmp(modifier,'control') % Perform certain actions or take a big slice step in the currect view
                    switch key
                        case '1'
                            TranslationAlign12ButtonPushed(app)
                        case '2'
                            RotationalAlign1234ButtonPushed(app)
                        case 'r'
                            app.RotateAssistButtonPushed(app)
                        case 'rightarrow'
                            app.Down50ButtonPushed(app)
                        case 'leftarrow'
                            app.Up50ButtonPushed(app)
                        case 's' % ctrl + s uses defaults while manually pressing the equivalent buttons provides the user with choices
                            fig = uifigure;
                            selection = uiconfirm(fig,'Proceed with overwriting?','Overwrite','Icon','warning');
                            delete(fig)
                            switch selection
                                case 'Cancel'
                                    return
                            end
                            SaveMatching(app, true) % overwrites
                            SaveAllKnots(app, true) % overwrites
                            NextDataButtonPushed(app) % Select next disk
                            loadData(app, true) % Reads defaut 'Dry'
                    end

                elseif strcmp(modifier(1),'shift') && strcmp(modifier(end), 'alt') % Combines the uses of 'shift' and 'alt' from above
                    tempstep = app.StepSize.Value;
                    tempangle = app.AngleSize.Value;
                    app.StepSize.Value = app.StepSize.Value/4;
                    app.AngleSize.Value = app.AngleSize.Value/4;
                    switch key
                        case 'r'
                            app.RotatePButtonPushed(app)
                        case 'z'
                            app.ZmButtonPushed(app)
                        case 'q'
                            app.YawMButtonPushed(app)
                        case 'e'
                            app.PitchMButtonPushed(app)
                    end
                    app.StepSize.Value = tempstep;
                    app.AngleSize.Value = tempangle;
                elseif strcmp(modifier(1),'control') && strcmp(modifier(end), 'alt') % Moves to the slice ends of the current view
                    switch key
                        case 'rightarrow'
                            DownButtonPushed(app)
                        case 'leftarrow'
                            UpButtonPushed(app)
                    end
                end
            else
                switch key
                    case 'd'
                        app.XpButtonPushed(app)
                    case 'a'
                        app.XmButtonPushed(app)
                    case 'w'
                        app.YmButtonPushed(app)
                    case 's'
                        app.YpButtonPushed(app)
                    case 'r'
                        app.RotateMButtonPushed(app)
                    case 'z'
                        app.ZpButtonPushed(app)
                    case 'q'
                        app.YawPButtonPushed(app)
                    case 'e'
                        app.PitchPButtonPushed(app)
                    case '1'
                        app.WetTopPointStoreButtonPushed(app)
                    case '2'
                        app.DryTopPointStoreButtonPushed(app)
                    case '3'
                        app.WetButtPointStoreButtonPushed(app)
                    case '4'
                        app.DryButtPointStoreButtonPushed(app)
                    case '5'
                        app.WhorlStartStoreButtonPushed(app)
                    case 'f'
                        updateDisplayMode(app, 'falsecolor')
                    case 'm'
                        updateDisplayMode(app, 'montage')
                    case 'rightarrow'
                        EndDrySliderPButtonPushed(app)
                    case 'leftarrow'
                        EndDrySliderMButtonPushed(app)
                    case 'uparrow' % Unlocks slice sliders to move them independently
                        app.LockslicestogetherButton.Value = 0;
                        app.LockslicestogetherButtonValueChanged(app)
                    case 'downarrow' % Locks slice sliders to move them in unison
                        app.LockslicestogetherButton.Value = 1;
                        app.LockslicestogetherButtonValueChanged(app)
                    case 'escape'
                        focus(app.CTRegistratorUIFigure)
                        if strcmp(getenv('username'),'Linus')
                            keyboard
                        end
                    case 'return'
                        if strcmp(app.TabGroup.SelectedTab.Title, 'Knots')
                            UpdateKnotMarkingsButtonPushed(app)
                        elseif strcmp(app.TabGroup.SelectedTab.Title, 'End')
                            updateView(app)
                        end
                end
            end
        end

        % Value changed function: StepSize
        function StepSizeValueChanged(app, event)
            if app.StepSize.Value <= 0
                app.StepSize.Value = 1;
                beep
                fprintf('StepSize value can not be negative or 0\n')
            end

            focus(app.CTRegistratorUIFigure)
        end

        % Value changed function: ContrastCheckBox
        function ContrastCheckBoxValueChanged(app, event)
            updateView(app)
        end

        % Button pushed function: SideWetSliderM
        function SideWetSliderMButtonPushed(app, event)
            app.SideWetSlider.Value = max(app.SideWetSlider.Value-app.sliceStep,app.SideWetSlider.Limits(1));
            updateView(app)
        end

        % Button pushed function: SideWetSliderP
        function SideWetSliderPButtonPushed(app, event)
            app.SideWetSlider.Value = min(app.SideWetSlider.Value+app.sliceStep,app.SideWetSlider.Limits(2));
            updateView(app)
        end

        % Button pushed function: SideDrySliderM
        function SideDrySliderMButtonPushed(app, event)
            if app.LockslicestogetherButton.Value
                whorlstep = max(app.SideDrySlider.Limits(1), app.SideDrySlider.Value - app.sliceStep) - app.SideDrySlider.Value;
                logstep = max(app.SideWetSlider.Limits(1), app.SideWetSlider.Value - app.sliceStep) - app.SideWetSlider.Value;

                step = max(whorlstep,logstep);

                app.SideDrySlider.Value = app.SideDrySlider.Value + step;
                app.SideWetSlider.Value = app.SideWetSlider.Value + step;
            else
                app.SideDrySlider.Value = max(app.SideDrySlider.Limits(1), app.SideDrySlider.Value - app.sliceStep);
            end
            updateView(app)
        end

        % Button pushed function: SideDrySliderP
        function SideDrySliderPButtonPushed(app, event)
            if app.LockslicestogetherButton.Value
                whorlstep = min(app.SideDrySlider.Limits(2), app.SideDrySlider.Value + app.sliceStep) - app.SideDrySlider.Value;
                logstep = min(app.SideWetSlider.Limits(2), app.SideWetSlider.Value + app.sliceStep) - app.SideWetSlider.Value;

                step = min(whorlstep,logstep);

                app.SideDrySlider.Value = app.SideDrySlider.Value + step;
                app.SideWetSlider.Value = app.SideWetSlider.Value + step;
            else
                app.SideDrySlider.Value = min(app.SideDrySlider.Limits(2), app.SideDrySlider.Value + app.sliceStep);
            end
            updateView(app)
        end

        % Button pushed function: TopWetSliderM
        function TopWetSliderMButtonPushed(app, event)
            app.TopWetSlider.Value = max(app.TopWetSlider.Value-app.sliceStep,app.TopWetSlider.Limits(1));
            updateView(app)
        end

        % Button pushed function: TopWetSliderP
        function TopWetSliderPButtonPushed(app, event)
            app.TopWetSlider.Value = min(app.TopWetSlider.Value+app.sliceStep,app.TopWetSlider.Limits(2));
            updateView(app)
        end

        % Button pushed function: TopDrySliderM
        function TopDrySliderMButtonPushed(app, event)
            if app.LockslicestogetherButton.Value
                whorlstep = max(app.TopDrySlider.Limits(1), app.TopDrySlider.Value - app.sliceStep) - app.TopDrySlider.Value;
                logstep = max(app.TopWetSlider.Limits(1), app.TopWetSlider.Value - app.sliceStep) - app.TopWetSlider.Value;

                step = max(whorlstep,logstep);

                app.TopDrySlider.Value = app.TopDrySlider.Value + step;
                app.TopWetSlider.Value = app.TopWetSlider.Value + step;
            else
                app.TopDrySlider.Value = max(app.TopDrySlider.Limits(1), app.TopDrySlider.Value - app.sliceStep);
            end
            updateView(app)
        end

        % Button pushed function: TopDrySliderP
        function TopDrySliderPButtonPushed(app, event)
            if app.LockslicestogetherButton.Value
                whorlstep = min(app.TopDrySlider.Limits(2), app.TopDrySlider.Value + app.sliceStep) - app.TopDrySlider.Value;
                logstep = min(app.TopWetSlider.Limits(2), app.TopWetSlider.Value + app.sliceStep) - app.TopWetSlider.Value;

                slicestep = min(whorlstep,logstep);

                app.TopDrySlider.Value = app.TopDrySlider.Value + slicestep;
                app.TopWetSlider.Value = app.TopWetSlider.Value + slicestep;
            else
                app.TopDrySlider.Value = min(app.TopDrySlider.Limits(2), app.TopDrySlider.Value + app.sliceStep);
            end
            updateView(app)
        end

        % Button pushed function: EndWetSliderM
        function EndWetSliderMButtonPushed(app, event)
            app.EndWetSlider.Value = max(app.EndWetSlider.Value-app.sliceStep,app.EndWetSlider.Limits(1));
            updateView(app)
        end

        % Button pushed function: EndWetSliderP
        function EndWetSliderPButtonPushed(app, event)
            app.EndWetSlider.Value = min(app.EndWetSlider.Value+app.sliceStep,app.EndWetSlider.Limits(2));
            updateView(app)
        end

        % Button pushed function: EndDrySliderM
        function EndDrySliderMButtonPushed(app, event)
            if app.LockslicestogetherButton.Value
                whorlstep = max(app.EndDrySlider.Limits(1), app.EndDrySlider.Value - app.sliceStep) - app.EndDrySlider.Value;
                logstep = max(app.EndWetSlider.Limits(1), app.EndWetSlider.Value - app.sliceStep) - app.EndWetSlider.Value;

                step = max(whorlstep,logstep);

                app.EndDrySlider.Value = app.EndDrySlider.Value + step;
                app.EndWetSlider.Value = app.EndWetSlider.Value + step;
            else
                app.EndDrySlider.Value = max(app.EndDrySlider.Limits(1), app.EndDrySlider.Value - app.sliceStep);
            end
            updateView(app)
        end

        % Button pushed function: EndDrySliderP
        function EndDrySliderPButtonPushed(app, event)
            if app.LockslicestogetherButton.Value
                whorlstep = min(app.EndDrySlider.Limits(2), app.EndDrySlider.Value + app.sliceStep) - app.EndDrySlider.Value;
                logstep = min(app.EndWetSlider.Limits(2), app.EndWetSlider.Value + app.sliceStep) - app.EndWetSlider.Value;

                slicestep = min(whorlstep,logstep);

                app.EndDrySlider.Value = app.EndDrySlider.Value + slicestep;
                app.EndWetSlider.Value = app.EndWetSlider.Value + slicestep;
            else
                app.EndDrySlider.Value = min(app.EndDrySlider.Limits(2), app.EndDrySlider.Value + app.sliceStep);
            end
            updateView(app)
        end

        % Value changed function: FalsecolorCheckBox
        function FalsecolorCheckBoxValueChanged(app, event)
            updateDisplayMode(app, 'falsecolor')
        end

        % Value changed function: DifferenceCheckBox
        function DifferenceCheckBoxValueChanged(app, event)
            if app.DifferenceCheckBox.Value; updateDisplayMode(app, 'diff'); else; updateDisplayMode(app, 'falsecolor'); end
        end

        % Value changed function: MontageCheckBox
        function MontageCheckBoxValueChanged(app, event)
            if app.MontageCheckBox.Value; updateDisplayMode(app, 'montage'); else; updateDisplayMode(app, 'falsecolor'); end
        end

        % Button pushed function: WetTopPointStoreButton
        function WetTopPointStoreButtonPushed(app, event)
            if ~app.WetTopPointStoreButton.Enable; return; end
            app.RotationalAlign1234Button.Enable = 0;
            app.TranslationAlign12Button.Enable = 0;
            
            app.WetTopPointStoreEditField.Value = app.CursorEditField.Value;
            app.WetTopPointSliceEditField.Value = num2str(app.EndWetSlider.Value);
            if ~isempty(app.WetTopPointStoreEditField.Value) && ~isempty(app.DryTopPointStoreEditField.Value) && ~isempty(app.WetButtPointStoreEditField.Value) && ~isempty(app.DryButtPointStoreEditField.Value)
                app.RotationalAlign1234Button.Enable = 1;
            elseif ~isempty(app.WetTopPointStoreEditField.Value) && ~isempty(app.DryTopPointStoreEditField.Value)
                app.TranslationAlign12Button.Enable = 1;
            end
            updateView(app)
        end

        % Button pushed function: DryTopPointStoreButton
        function DryTopPointStoreButtonPushed(app, event)
            if ~app.DryTopPointStoreButton.Enable; return; end
            app.TranslationAlign12Button.Enable = 0;
            app.RotationalAlign1234Button.Enable = 0;


            app.DryTopPointStoreEditField.Value = app.CursorEditField.Value;
            app.DryTopPointSliceEditField.Value = num2str(app.EndDrySlider.Value);

            if ~isempty(app.WetTopPointStoreEditField.Value) && ~isempty(app.DryTopPointStoreEditField.Value) && ~isempty(app.WetButtPointStoreEditField.Value) && ~isempty(app.DryButtPointStoreEditField.Value)
                app.RotationalAlign1234Button.Enable = 1;
            elseif ~isempty(app.WetTopPointStoreEditField.Value) && ~isempty(app.DryTopPointStoreEditField.Value)
                app.TranslationAlign12Button.Enable = 1;
            end
            updateView(app)
        end

        % Button pushed function: WetButtPointStoreButton
        function WetButtPointStoreButtonPushed(app, event)
            if ~app.WetButtPointStoreButton.Enable; return; end
            app.RotationalAlign1234Button.Enable = 0;
            
            app.WetButtPointStoreEditField.Value = app.CursorEditField.Value;
            app.WetButtPointSliceEditField.Value = num2str(app.EndWetSlider.Value);
            if ~isempty(app.WetTopPointStoreEditField.Value) && ~isempty(app.DryTopPointStoreEditField.Value) && ~isempty(app.WetButtPointStoreEditField.Value) && ~isempty(app.DryButtPointStoreEditField.Value)
                app.RotationalAlign1234Button.Enable = 1;
            end
            updateView(app)
        end

        % Button pushed function: DryButtPointStoreButton
        function DryButtPointStoreButtonPushed(app, event)
            if ~app.DryButtPointStoreButton.Enable; return; end
            app.RotationalAlign1234Button.Enable = 0;
            
            app.DryButtPointStoreEditField.Value = app.CursorEditField.Value;
            app.DryButtPointSliceEditField.Value = num2str(app.EndDrySlider.Value);

            if ~isempty(app.WetTopPointStoreEditField.Value) && ~isempty(app.DryTopPointStoreEditField.Value) && ~isempty(app.WetButtPointStoreEditField.Value) && ~isempty(app.DryButtPointStoreEditField.Value)
                app.RotationalAlign1234Button.Enable = 1;
            end
            updateView(app)
        end

        % Value changed function: LockslicestogetherButton
        function LockslicestogetherButtonValueChanged(app, event)
            app.SideWetSlider.Enable = ~app.LockslicestogetherButton.Value;
            app.SideWetSliderM.Enable = ~app.LockslicestogetherButton.Value;
            app.SideWetSliderP.Enable = ~app.LockslicestogetherButton.Value;

            app.TopWetSlider.Enable = ~app.LockslicestogetherButton.Value;
            app.TopWetSliderM.Enable = ~app.LockslicestogetherButton.Value;
            app.TopWetSliderP.Enable = ~app.LockslicestogetherButton.Value;

            app.EndWetSlider.Enable = ~app.LockslicestogetherButton.Value;
            app.EndWetSliderM.Enable = ~app.LockslicestogetherButton.Value;
            app.EndWetSliderP.Enable = ~app.LockslicestogetherButton.Value;

            app.SideDrySlider.Enable = ~app.LockslicestogetherButton.Value;

            app.TopDrySlider.Enable = ~app.LockslicestogetherButton.Value;

            app.EndDrySlider.Enable = ~app.LockslicestogetherButton.Value;

            focus(app.CTRegistratorUIFigure)
        end

        % Button pushed function: Down50Button
        function Down50ButtonPushed(app, event)
            if app.LockslicestogetherButton.Value
                whorlstep = min(app.EndDrySlider.Limits(2), app.EndDrySlider.Value + 50) - app.EndDrySlider.Value;
                logstep = min(app.EndWetSlider.Limits(2), app.EndWetSlider.Value + 50) - app.EndWetSlider.Value;

                slicestep = min(whorlstep,logstep);

                app.EndDrySlider.Value = app.EndDrySlider.Value + slicestep;
                app.EndWetSlider.Value = app.EndWetSlider.Value + slicestep;
            else
                app.EndDrySlider.Value = min(app.EndDrySlider.Limits(2), app.EndDrySlider.Value + 50);
            end
            updateView(app)
        end

        % Button pushed function: Up50Button
        function Up50ButtonPushed(app, event)
            if app.LockslicestogetherButton.Value
                whorlstep = max(app.EndDrySlider.Limits(1), app.EndDrySlider.Value - 50) - app.EndDrySlider.Value;
                logstep = max(app.EndWetSlider.Limits(1), app.EndWetSlider.Value - 50) - app.EndWetSlider.Value;

                slicestep = max(whorlstep,logstep);

                app.EndDrySlider.Value = app.EndDrySlider.Value + slicestep;
                app.EndWetSlider.Value = app.EndWetSlider.Value + slicestep;
            else
                app.EndDrySlider.Value = min(app.EndDrySlider.Limits(2), app.EndDrySlider.Value - 50);
            end
            updateView(app)
        end

        % Button pushed function: TranslationAlign12Button
        function TranslationAlign12ButtonPushed(app, event)
            if~app.TranslationAlign12Button.Enable; beep; return; end
            TranslateWetTopToDryTopIn3D(app)
        end

        % Button pushed function: RotationalAlign1234Button
        function RotationalAlign1234ButtonPushed(app, event)
            if~app.RotationalAlign1234Button.Enable; beep; return; end
            AlignWetButtWithDryButtGivenWetTopAndDryTop(app)
        end

        % Value changed function: AngleSize
        function AngleSizeValueChanged(app, event)
            if app.AngleSize.Value <= 0
                app.AngleSize.Value = 1;
                beep
                fprintf("AngleSize can't be negative or 0\n")
            end

            focus(app.CTRegistratorUIFigure)
        end

        % Button pushed function: PitchPButton
        function PitchPButtonPushed(app, event)
            if ~app.PitchPButton.Enable; return; end
            AlignWetButtWithDryButtGivenWetTopAndDryTop(app, app.AngleSize.Value, 0)
        end

        % Button pushed function: PitchMButton
        function PitchMButtonPushed(app, event)
            if ~app.PitchMButton.Enable; return; end
            AlignWetButtWithDryButtGivenWetTopAndDryTop(app,-app.AngleSize.Value, 0)
        end

        % Button pushed function: YawPButton
        function YawPButtonPushed(app, event)
            if ~app.YawPButton.Enable; return; end
            AlignWetButtWithDryButtGivenWetTopAndDryTop(app, 0, app.AngleSize.Value)
        end

        % Button pushed function: YawMButton
        function YawMButtonPushed(app, event)
            if ~app.YawMButton.Enable; return; end
            AlignWetButtWithDryButtGivenWetTopAndDryTop(app, 0,-app.AngleSize.Value)
        end

        % Value changed function: EndWetSlider
        function EndWetSliderValueChanged(app, event)
            app.EndWetSlider.Value = round(app.EndWetSlider.Value);
            updateView(app)
        end

        % Value changed function: EndDrySlider
        function EndDrySliderValueChanged(app, event)
            app.EndDrySlider.Value = round(app.EndDrySlider.Value);
            updateView(app)
        end

        % Value changed function: SideWetSlider
        function SideWetSliderValueChanged(app, event)
            app.SideWetSlider.Value = round(app.SideWetSlider.Value);
            updateView(app)
        end

        % Value changed function: SideDrySlider
        function SideDrySliderValueChanged(app, event)
            app.SideDrySlider.Value = round(app.SideDrySlider.Value);
            updateView(app)
        end

        % Value changed function: TopWetSlider
        function TopWetSliderValueChanged(app, event)
            app.TopWetSlider.Value = round(app.TopWetSlider.Value);
            updateView(app)
        end

        % Value changed function: TopDrySlider
        function TopDrySliderValueChanged(app, event)
            app.TopDrySlider.Value = round(app.TopDrySlider.Value);
            updateView(app)
        end

        % Value changed function: LockOriginsButton
        function LockOriginsButtonValueChanged(app, event)
            if app.LockOriginsButton.Value
                app.XpButton.Enable = 0;
                app.XmButton.Enable = 0;
                app.YpButton.Enable = 0;
                app.YmButton.Enable = 0;
                app.ZpButton.Enable = 0;
                app.ZmButton.Enable = 0;
                app.StepSize.Enable = 0;
                app.WetTopPointStoreButton.Enable = 0;
                app.DryTopPointStoreButton.Enable = 0;
                app.TranslationAlign12Button.Enable = 0;
                
                app.LockPointsButton.Enable = 1;

                app.PitchPButton.Enable = 1;
                app.PitchMButton.Enable = 1;
                app.YawPButton.Enable = 1;
                app.YawMButton.Enable = 1;
                if ~isempty(app.DryButtPointStoreEditField.Value)
                    app.RotationalAlign1234Button.Enable = 1;
                else
                    app.RotationalAlign1234Button.Enable = 0;
                end
            else
                app.XpButton.Enable = 1;
                app.XmButton.Enable = 1;
                app.YpButton.Enable = 1;
                app.YmButton.Enable = 1;
                app.ZpButton.Enable = 1;
                app.ZmButton.Enable = 1;
                app.StepSize.Enable = 1;
                app.WetTopPointStoreButton.Enable = 1;
                app.DryTopPointStoreButton.Enable = 1;
                app.TranslationAlign12Button.Enable = 1;
                
                app.LockPointsButton.Enable = 0;

                app.PitchPButton.Enable = 0;
                app.PitchMButton.Enable = 0;
                app.YawPButton.Enable = 0;
                app.YawMButton.Enable = 0;

                app.RotationalAlign1234Button.Enable = 0;
            end
            
            focus(app.CTRegistratorUIFigure)
        end

        % Value changed function: LockPointsButton
        function LockPointsButtonValueChanged(app, event)
            if app.LockPointsButton.Value
                app.RotatePButton.Enable = 0;
                app.RotateMButton.Enable = 0;
                app.RotateAssistButton.Enable = 0;
                app.YawPButton.Enable = 0;
                app.YawMButton.Enable = 0;
                app.PitchPButton.Enable = 0;
                app.PitchMButton.Enable = 0;
                app.AngleSize.Enable = 0;
                app.LockOriginsButton.Enable = 0;
                app.TranslationAlign12Button.Enable = 0;
                app.RotationalAlign1234Button.Enable = 0;
                app.WetButtPointStoreButton.Enable = 0;
                app.DryButtPointStoreButton.Enable = 0;
            else
                app.RotatePButton.Enable = 1;
                app.RotateMButton.Enable = 1;
                app.RotateAssistButton.Enable = 1;
                app.YawPButton.Enable = 1;
                app.YawMButton.Enable = 1;
                app.PitchPButton.Enable = 1;
                app.PitchMButton.Enable = 1;
                app.AngleSize.Enable = 1;
                app.RotationalAlign1234Button.Enable = 1;
                app.WetButtPointStoreButton.Enable = 1;
                app.DryButtPointStoreButton.Enable = 1;
                app.LockOriginsButton.Enable = 1;
            end
            
            % if app.LockOriginsButton.Value && app.LockPointsButton.Value
            %     app.SavematchedwhorlButton.Enable = 1;
            % else
            %     app.SavematchedwhorlButton.Enable = 0;
            % end

            focus(app.CTRegistratorUIFigure)
        end

        % Button pushed function: UpButton
        function UpButtonPushed(app, event)
            if app.LockslicestogetherButton.Value
                whorlstep = max(app.EndDrySlider.Limits(1), app.EndDrySlider.Value - 500) - app.EndDrySlider.Value;
                logstep = max(app.EndWetSlider.Limits(1), app.EndWetSlider.Value - 500) - app.EndWetSlider.Value;

                slicestep = max(whorlstep,logstep);

                app.EndDrySlider.Value = app.EndDrySlider.Value + slicestep;
                app.EndWetSlider.Value = app.EndWetSlider.Value + slicestep;
            else
                app.EndDrySlider.Value = max(app.EndDrySlider.Limits(1), app.EndDrySlider.Value - 500);
            end
            updateView(app)
        end

        % Button pushed function: DownButton
        function DownButtonPushed(app, event)
            if app.LockslicestogetherButton.Value
                whorlstep = min(app.EndDrySlider.Limits(2), app.EndDrySlider.Value + 500) - app.EndDrySlider.Value;
                logstep = min(app.EndWetSlider.Limits(2), app.EndWetSlider.Value + 500) - app.EndWetSlider.Value;

                slicestep = min(whorlstep,logstep);

                app.EndDrySlider.Value = app.EndDrySlider.Value + slicestep;
                app.EndWetSlider.Value = app.EndWetSlider.Value + slicestep;
            else
                app.EndDrySlider.Value = min(app.EndDrySlider.Limits(2), app.EndDrySlider.Value + 500);
            end
            updateView(app)
        end

        % Button pushed function: SavematchedwhorlButton
        function SavematchedwhorlButtonPushed(app, event)
            SaveMatching(app)
        end

        % Selection change function: TabGroup
        function TabGroupSelectionChanged(app, event)
            focus(app.CTRegistratorUIFigure)
        end

        % Value changed function: BrightnessadjCheckBox
        function BrightnessadjCheckBoxValueChanged(app, event)
            updateView(app)
        end

        % Button pushed function: RotateAssistButton
        function RotateAssistButtonPushed(app, event)
            if ~app.RotateAssistButton.Enable; return; end
            RotateToAlignWetButtWithDryButtInEndViewIn2D(app)
        end

        % Button pushed function: WhorlStartStoreButton
        function WhorlStartStoreButtonPushed(app, event)
            % Check if the user is viewing different slices, which might mean that the user thinks they have aligned the bodies but forgot to press the 'app.TranslationAlign12Button' (or ctrl+1) button.
            adjustSliceDifference(app)
            
            % Check how the user is trying to assign a Knot_start value
            EventIsManualEntry = 0;
            if strcmp(class(event), 'CTRegistrator') % '5' on keyboard was pressed
                if isempty(app.CursorEditField.Value)
                    error("Cursor coordinates empty. Place the cursor at the knot (whorl) start in the Dry disk in the End view and press key '5'.")
                else
                    try
                        slices = str2num(app.SlicesEditField.Value);
                        app.KnotStartStoreEditField.Value = [app.CursorEditField.Value ',  ' num2str(slices(2))];
                    catch
                        error("Could not capture Knot start.")
                    end
                end
            elseif strcmp(event.EventName, 'ButtonPushed') % The button itself was pushed
                error("Can't press '5' directly. Mark the knot (whorl) start in the Dry disk in the End view using the mouse cursor + key-press '5'.")
            else % event.EventName is 'ValueChanged', meaning the edit field was manually edited.
                EventIsManualEntry = 1;
            end

            % Assign the same Knot_start value to all Knot_start(i>=iknot) to populate each cell.
            nr_of_knots = size(app.KnotDataStruct.KNOT_NO,1);
            
            for i = str2num(app.KnotDropDown.Value):nr_of_knots
                app.KnotDataStruct.Knot_start(i, :) = str2num(app.KnotStartStoreEditField.Value);
            end

            updateKnotDataStructWithUI(app)
            app.SaveallknotsButton.BackgroundColor = [0.96 0.96 0.96];
            
            % Initiate the knot matching process.
            if ~isempty(app.KnotStartStoreEditField.Value)
                app.TabGroup.SelectedTab = app.KnotsTab;
                updateAzimuthEndView(app)
                if EventIsManualEntry && app.ConfirmAzimuthButton.Value
                    updateKnotCrossSectionView(app)
                end
            end
        end

        % Value changed function: KnotDropDown
        function KnotDropDownValueChanged(app, event)
            % First save the current UI to KnotDataStruct
            try % event.PreviousValue exists when the dropdown menue was used to change the value...
                iknot_prev = str2num(event.PreviousValue); % For some reason, anything similar to "exist(...)" does not work on event.PreviousValue when it does not exist... ecent is "ValueChangedData" and not an ordinary struct.
                updateKnotDataStructWithUI(app,iknot_prev)
            catch 
                % ... If not, it's because the value was changed usign the "Next Knot" button, meaning the value has already been changed and the KnotDataStruct update was performed in that function.
            end
            
            % Then, load new data from the KnotDataStruct and write it to the UI.    
            updateKnotUIFromKnotDataStruct(app)
            

            % UI suff
            % Reset Knot Cross Section View (removes previous sliceViewer).
            position = app.KnotCrossSectionViewPanel.Position;
            title = app.KnotCrossSectionViewPanel.Title;

            % Delete existing panel, replace it, then plot the sliceViewer
            delete(app.KnotCrossSectionViewPanel)
            app.KnotCrossSectionViewPanel = uipanel('Title',title,'Position',position,'Parent',app.KnotsTab);

            if strcmp(app.KnotDropDown.Value,app.KnotDropDown.Items{end})
                app.NextKnotButton.Enable = 0;
            end

            app.ConfirmAzimuthButton.Value = 0;            
            updateAzimuthEndView(app)
        end

        % Value changed function: ConfirmAzimuthButton
        function ConfirmAzimuthButtonValueChanged(app, event)
            app.ConfirmAzimuthButton.Enable = 0;
            UpdateKnotMarkingsButtonPushed(app)
            ConfigureUI(app)
        end

        % Button pushed function: AzimuthPButton
        function AzimuthPButtonPushed(app, event)
            if app.AzimuthEditField.Value >= 359
                app.AzimuthEditField.Value = 0;
            else
                app.AzimuthEditField.Value = app.AzimuthEditField.Value + 1;
            end

            app.ConfirmAzimuthButton.Enable = 1;
            app.ConfirmAzimuthButton.Value = 0;

            updateKnotDataStructWithUI(app)
        end

        % Button pushed function: AzimuthMButton
        function AzimuthMButtonPushed(app, event)
            if app.AzimuthEditField.Value <= 1
                app.AzimuthEditField.Value = 359;
            else
                app.AzimuthEditField.Value = app.AzimuthEditField.Value - 1;
            end

            app.ConfirmAzimuthButton.Enable = 1;
            app.ConfirmAzimuthButton.Value = 0;

            updateKnotDataStructWithUI(app)
        end

        % Value changed function: AzimuthEditField
        function AzimuthEditFieldValueChanged(app, event)
            app.ConfirmAzimuthButton.Enable = 1;
            app.ConfirmAzimuthButton.Value = 0;

            app.AzimuthEditField.Value = mod(app.AzimuthEditField.Value, 360);

            updateKnotDataStructWithUI(app)

            updateAzimuthEndView(app)
        end

        % Button pushed function: UpdateKnotMarkingsButton
        function UpdateKnotMarkingsButtonPushed(app, event)
            if isempty(app.KnotStartStoreEditField.Value)
                beep
                m = msgbox('Mark the start of the whorl first (5) in the End view.');
                pause(5)
                delete(m)
                return
            end

            updateKnotDataStructWithUI(app)
            
            updateAzimuthEndView(app)
            if app.ConfirmAzimuthButton.Value
                updateKnotCrossSectionView(app)
            end
            app.TabGroup.SelectedTab = app.KnotsTab;
        end

        % Button pushed function: L4PButton
        function L4PButtonPushed(app, event)
            app.L4EditField.Value = app.L4EditField.Value + 1;
            updateKnotDataStructWithUI(app)
        end

        % Button pushed function: L4MButton
        function L4MButtonPushed(app, event)
            app.L4EditField.Value = app.L4EditField.Value - 1;
            updateKnotDataStructWithUI(app)
        end

        % Button pushed function: D1PButton
        function D1PButtonPushed(app, event)
            app.DiameterEditField.Value = app.DiameterEditField.Value + 1;
            updateKnotDataStructWithUI(app)
        end

        % Button pushed function: D1MButton
        function D1MButtonPushed(app, event)
            app.DiameterEditField.Value = app.DiameterEditField.Value - 1;
            updateKnotDataStructWithUI(app)
        end

        % Button pushed function: L1aPButton
        function L1aPButtonPushed(app, event)
            app.L1aEditField.Value = app.L1aEditField.Value + 1;
            if ~app.DeadCheckBox.Value % If Green knot, L1a controls L1b also
                app.L1bEditField.Value = app.L1bEditField.Value + 1;
            end
            updateKnotDataStructWithUI(app)
        end

        % Button pushed function: L1aMButton
        function L1aMButtonPushed(app, event)
            app.L1aEditField.Value = app.L1aEditField.Value - 1;
            if ~app.DeadCheckBox.Value % If Green knot, L1a controls L1b also
                app.L1bEditField.Value = app.L1bEditField.Value - 1;
            end
            updateKnotDataStructWithUI(app)
        end

        % Button pushed function: L1bPButton
        function L1bPButtonPushed(app, event)
            app.L1bEditField.Value = app.L1bEditField.Value + 1;
            updateKnotDataStructWithUI(app)
        end

        % Button pushed function: L1bMButton
        function L1bMButtonPushed(app, event)
            app.L1bEditField.Value = app.L1bEditField.Value - 1;
            updateKnotDataStructWithUI(app)
        end

        % Button pushed function: NextKnotButton
        function NextKnotButtonPushed(app, event)
            % Save current UI Knot values to KnotDataStruct befor changing the drop down value.
            updateKnotDataStructWithUI(app)

            app.KnotDropDown.Value = app.KnotDropDown.Items{min(str2num(app.KnotDropDown.Value)+1, length(app.KnotDropDown.Items))};
            KnotDropDownValueChanged(app, event)
        end

        % Button pushed function: LoadKnotDataButton
        function LoadKnotDataButtonPushed(app, event)
            loadKnots(app)
        end

        % Button pushed function: NextDataButton
        function NextDataButtonPushed(app, event)
            wetItemIndex = find(strcmp(app.SelectedWetFileDropDown.Items,app.SelectedWetFileDropDown.Value));
            wetItemIndex = 1 + mod(wetItemIndex, numel(app.SelectedWetFileDropDown.Items));
            app.SelectedWetFileDropDown.Value = app.SelectedWetFileDropDown.Items(wetItemIndex);

            SelectedWetFileDropDownValueChanged(app, struct('Value',app.SelectedWetFileDropDown.Value))

            if wetItemIndex == 1 % No more disks: mod above resets index to 1 and next tree needs to be seclected.
                treeItemIndex = find(strcmp(app.SelectedTreeDropDown.Items,app.SelectedTreeDropDown.Value));
                treeItemIndex = 1 + mod(treeItemIndex, numel(app.SelectedTreeDropDown.Items));
                app.SelectedTreeDropDown.Value = app.SelectedTreeDropDown.Items(treeItemIndex);
                SelectedTreeDropDownValueChanged(app, struct('Value',app.SelectedTreeDropDown.Value));
            end

            % app.LoadDataButton.Enable = 0;
            % loadData(app, true) % Load default 'Dry' data and default 'Dry' knot data source
            % pause(1)
            % app.LoadDataButton.Enable = 1;
        end

        % Button pushed function: SaveallknotsButton
        function SaveallknotsButtonPushed(app, event)
            SaveAllKnots(app)
        end

        % Value changed function: KnotStartStoreEditField
        function KnotStartStoreEditFieldValueChanged(app, event)
            WhorlStartStoreButtonPushed(app,event)
        end

        % Value changed function: L4EditField
        function L4EditFieldValueChanged(app, event)
            app.KnotDataStruct.L4(str2num(app.KnotDropDown.Value)) = app.L4EditField.Value;
            UpdateKnotMarkingsButtonPushed(app, event)
        end

        % Value changed function: DiameterEditField
        function DiameterEditFieldValueChanged(app, event)
        app.KnotDataStruct.D1(str2num(app.KnotDropDown.Value)) = app.DiameterEditField.Value;
        UpdateKnotMarkingsButtonPushed(app, event)
        end

        % Value changed function: DeadCheckBox
        function DeadCheckBoxValueChanged(app, event)
            if app.DeadCheckBox.Value
                app.KnotDataStruct.Knot_type{str2num(app.KnotDropDown.Value)} = 'D';
            else
                app.KnotDataStruct.Knot_type{str2num(app.KnotDropDown.Value)} = 'G';
            end
            updateKnotDataStructWithUI(app)
        end

        % Value changed function: L1aEditField
        function L1aEditFieldValueChanged(app, event)
            app.KnotDataStruct.L1_a(str2num(app.KnotDropDown.Value)) = app.L1aEditField.Value;
            if ~app.DeadCheckBox.Value % If Green knot, L1a controls L1b also
                app.KnotDataStruct.L1_b(str2num(app.KnotDropDown.Value)) = app.L1aEditField.Value;
                app.L1bEditField.Value = app.L1aEditField.Value;
            end
            UpdateKnotMarkingsButtonPushed(app, event)
        end

        % Value changed function: L1bEditField
        function L1bEditFieldValueChanged(app, event)
            app.KnotDataStruct.L1_b(str2num(app.KnotDropDown.Value)) = app.L1bEditField.Value;
            UpdateKnotMarkingsButtonPushed(app, event)
        end

        % Value changed function: L5EditField
        function L5EditFieldValueChanged(app, event)
            app.KnotDataStruct.L5(str2num(app.KnotDropDown.Value)) = app.L5EditField.Value;
            UpdateKnotMarkingsButtonPushed(app, event)
        end

        % Button pushed function: L5MButton
        function L5MButtonPushed(app, event)
            app.L5EditField.Value = app.L5EditField.Value - 1;
            updateKnotDataStructWithUI(app)
        end

        % Button pushed function: L5PButton
        function L5PButtonPushed(app, event)
            app.L5EditField.Value = app.L5EditField.Value + 1;
            updateKnotDataStructWithUI(app)
        end

        % Value changed function: DiscreteXrayCheckBox
        function DiscreteXrayCheckBoxValueChanged(app, event)
            updateView(app)
        end

        % Value changed function: CropKCSviewCheckBox
        function CropKCSviewCheckBoxValueChanged(app, event)
            % Reset the Knot Cross-section panel
            position = app.KnotCrossSectionViewPanel.Position;
            title = app.KnotCrossSectionViewPanel.Title;
            delete(app.KnotCrossSectionViewPanel)
            app.KnotCrossSectionViewPanel = uipanel('Title',title,'Position',position,'Parent',app.KnotsTab);

            UpdateKnotMarkingsButtonPushed(app)
        end

        % Button pushed function: AddknotButton
        function AddknotButtonPushed(app, event)
            if isempty(app.KnotDataStruct.Knot_ID_in_database)
                error('Cannot add a new knot to uninitialized knot data.')
            end

            % Add 1 new "row" to the KnotDataStruct
            fieldNames = fieldnames(app.KnotDataStruct);
            
            for i = 1:length(fieldNames)
                fieldName = fieldNames{i};
                
                if strcmp(fieldName, 'Knot_start')
                    app.KnotDataStruct.(fieldName)(end+1, :) = app.KnotDataStruct.(fieldName)(end, :);
                elseif strcmp(fieldName, 'KNOT_NO')
                    app.KnotDataStruct.(fieldName)(end+1, 1) = app.KnotDataStruct.(fieldName)(end, 1) + 1;
                elseif strcmp(fieldName, 'Knot_type')
                    app.KnotDataStruct.(fieldName){end+1, 1} = 'D'; % Assume 'Knot_type' is dead
                elseif strcmp(fieldName, 'Knot_ID_in_database')
                    % For the 'Knot_ID_in_database' field, increment the
                    % last number ('P.M.3.08.1.1.3' -> 'P.M.3.08.1.1.4')
                    lastID = app.KnotDataStruct.(fieldName){end, 1};
                    newID = incrementID(lastID);
                    app.KnotDataStruct.(fieldName){end+1, 1} = newID;
                elseif isnumeric(app.KnotDataStruct.(fieldName))
                    app.KnotDataStruct.(fieldName)(end+1, 1) = -1;
                end
            end
            
            updateKnotUIFromKnotDataStruct(app)

            % Helper function
            function newID = incrementID(lastID)
                parts = strsplit(lastID, '.');
                lastNumber = str2double(parts{end}) + 1;
                parts{end} = num2str(lastNumber);
                newID = strjoin(parts, '.');
            end
        end
    end

    % Component initialization
    methods (Access = private)

        % Create UIFigure and components
        function createComponents(app)
            % REMOVED
        end
    end

    % App creation and deletion
    methods (Access = public)
        % REMOVED
    end
end