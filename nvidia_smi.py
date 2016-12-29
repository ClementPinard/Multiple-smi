#####
# Copyright (c) 2011-2012, NVIDIA Corporation.  All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#    * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the NVIDIA Corporation nor the names of its
#      contributors may be used to endorse or promote products derived from
#      this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF 
# THE POSSIBILITY OF SUCH DAMAGE.
#####

#
# nvidia_smi
# nvml_bindings <at> nvidia <dot> com
#
# Sample code that attempts to reproduce the output of nvidia-smi -q- x
# For many cases the output should match
#
# To Run:
# $ python
# Python 2.7 (r27:82500, Sep 16 2010, 18:02:00) 
# [GCC 4.5.1 20100907 (Red Hat 4.5.1-3)] on linux2
# Type "help", "copyright", "credits" or "license" for more information.
# >>> import nvidia_smi
# >>> print(nvidia_smi.XmlDeviceQuery())
# ...
#

from pynvml import *
import datetime

#
# Helper functions
#
def GetEccByType(handle, counterType, errorType):
    strResult = ''
    
    try:
        deviceMemory = nvmlDeviceGetMemoryErrorCounter(handle, errorType, counterType,
                                                       NVML_MEMORY_LOCATION_DEVICE_MEMORY)
    except NVMLError as err:
        deviceMemory = handleError(err)
    strResult += '          <device_memory>' + str(deviceMemory) + '</device_memory>\n'
    
    try:
        registerFile = nvmlDeviceGetMemoryErrorCounter(handle, errorType, counterType,
                                                       NVML_MEMORY_LOCATION_REGISTER_FILE)
    except NVMLError as err:
        registerFile = handleError(err)
    
    strResult += '          <register_file>' + str(registerFile) + '</register_file>\n'
    
    try:
        l1Cache = nvmlDeviceGetMemoryErrorCounter(handle, errorType, counterType,
                                                  NVML_MEMORY_LOCATION_L1_CACHE)
    except NVMLError as err:
        l1Cache = handleError(err)
    strResult += '          <l1_cache>' + str(l1Cache) + '</l1_cache>\n'
    
    try:
        l2Cache = nvmlDeviceGetMemoryErrorCounter(handle, errorType, counterType,
                                                  NVML_MEMORY_LOCATION_L2_CACHE)
    except NVMLError as err:
        l2Cache = handleError(err)
    strResult += '          <l2_cache>' + str(l2Cache) + '</l2_cache>\n'
    
    try:
        textureMemory = nvmlDeviceGetMemoryErrorCounter(handle, errorType, counterType,
                                                        NVML_MEMORY_LOCATION_TEXTURE_MEMORY)
    except NVMLError as err:
        textureMemory = handleError(err)
    strResult += '          <texture_memory>' + str(textureMemory) + '</texture_memory>\n'
    
    try:
        count = str(nvmlDeviceGetTotalEccErrors(handle, errorType, counterType))
    except NVMLError as err:
        count = handleError(err)
    strResult += '          <total>' + count + '</total>\n'
    
    return strResult

def GetEccByCounter(handle, counterType):
    strResult = ''
    strResult += '        <single_bit>\n'
    strResult += str(GetEccByType(handle, counterType, NVML_MEMORY_ERROR_TYPE_CORRECTED))
    strResult += '        </single_bit>\n'
    strResult += '        <double_bit>\n'
    strResult += str(GetEccByType(handle, counterType, NVML_MEMORY_ERROR_TYPE_UNCORRECTED))
    strResult += '        </double_bit>\n'
    return strResult

def GetEccStr(handle):
    strResult = ''
    strResult += '      <volatile>\n'
    strResult += str(GetEccByCounter(handle, NVML_VOLATILE_ECC))
    strResult += '      </volatile>\n'
    strResult += '      <aggregate>\n'
    strResult += str(GetEccByCounter(handle, NVML_AGGREGATE_ECC))
    strResult += '      </aggregate>\n'
    return strResult

def StrGOM(mode):
    if mode == NVML_GOM_ALL_ON:
        return "All On";
    elif mode == NVML_GOM_COMPUTE:
        return "Compute";
    elif mode == NVML_GOM_LOW_DP:
        return "Low Double Precision";
    else:
        return "Unknown";

def GetClocksThrottleReasons(handle):
    throttleReasons = [
            [nvmlClocksThrottleReasonGpuIdle,           "clocks_throttle_reason_gpu_idle"],
            [nvmlClocksThrottleReasonUserDefinedClocks, "clocks_throttle_reason_user_defined_clocks"],
            [nvmlClocksThrottleReasonSwPowerCap,        "clocks_throttle_reason_sw_power_cap"],
            [nvmlClocksThrottleReasonHwSlowdown,        "clocks_throttle_reason_hw_slowdown"],
            [nvmlClocksThrottleReasonUnknown,           "clocks_throttle_reason_unknown"]
            ];

    strResult = ''

    try:
        supportedClocksThrottleReasons = nvmlDeviceGetSupportedClocksThrottleReasons(handle);
        clocksThrottleReasons = nvmlDeviceGetCurrentClocksThrottleReasons(handle);
        strResult += '    <clocks_throttle_reasons>\n'
        for (mask, name) in throttleReasons:
            if (mask & supportedClocksThrottleReasons):
                val = "Active" if mask & clocksThrottleReasons else "Not Active";
            else:
                val = handleError(NVML_ERROR_NOT_SUPPORTED);
            strResult += "      <%s>%s</%s>\n" % (name, val, name);
        strResult += '    </clocks_throttle_reasons>\n'
    except NVMLError as err:
        strResult += '    <clocks_throttle_reasons>%s</clocks_throttle_reasons>\n' % (handleError(err));

    return strResult;
        
#
# Converts errors into string messages
#
def handleError(err):
    if (err.value == NVML_ERROR_NOT_SUPPORTED):
        return "N/A"
    else:
        return err.__str__()

#######
def XmlDeviceQuery():

    try:
        #
        # Initialize NVML
        #
        nvmlInit()
        strResult = ''

        strResult += '<?xml version="1.0" ?>\n'
        strResult += '<!DOCTYPE nvidia_smi_log SYSTEM "nvsmi_device_v4.dtd">\n'
        strResult += '<nvidia_smi_log>\n'

        strResult += '  <timestamp>' + str(datetime.date.today()) + '</timestamp>\n'
        strResult += '  <driver_version>' + str(nvmlSystemGetDriverVersion()) + '</driver_version>\n'

        deviceCount = nvmlDeviceGetCount()
        strResult += '  <attached_gpus>' + str(deviceCount) + '</attached_gpus>\n'

        for i in range(0, deviceCount):
            handle = nvmlDeviceGetHandleByIndex(i)
            
            pciInfo = nvmlDeviceGetPciInfo(handle)    
            
            strResult += '  <gpu id="%s">\n' % pciInfo.busId
            
            strResult += '    <product_name>' + nvmlDeviceGetName(handle) + '</product_name>\n'
            
            try:
                state = ('Enabled' if (nvmlDeviceGetDisplayMode(handle) != 0) else 'Disabled')
            except NVMLError as err:
                state = handleError(err)
            
            strResult += '    <display_mode>' + state + '</display_mode>\n'
            
            try:
                mode = 'Enabled' if (nvmlDeviceGetPersistenceMode(handle) != 0) else 'Disabled'
            except NVMLError as err:
                mode = handleError(err)
            
            strResult += '    <persistence_mode>' + mode + '</persistence_mode>\n'
                
            strResult += '    <driver_model>\n'

            try:
                current = 'WDDM' if (nvmlDeviceGetCurrentDriverModel(handle) == NVML_DRIVER_WDDM) else 'TCC' 
            except NVMLError as err:
                current = handleError(err)
            strResult += '      <current_dm>' + current + '</current_dm>\n'

            try:
                pending = 'WDDM' if (nvmlDeviceGetPendingDriverModel(handle) == NVML_DRIVER_WDDM) else 'TCC' 
            except NVMLError as err:
                pending = handleError(err)

            strResult += '      <pending_dm>' + pending + '</pending_dm>\n'

            strResult += '    </driver_model>\n'

            try:
                serial = nvmlDeviceGetSerial(handle)
            except NVMLError as err:
                serial = handleError(err)

            strResult += '    <serial>' + serial + '</serial>\n'

            try:
                uuid = nvmlDeviceGetUUID(handle)
            except NVMLError as err:
                uuid = handleError(err)

            strResult += '    <uuid>' + uuid + '</uuid>\n'
            
            try:
                vbios = nvmlDeviceGetVbiosVersion(handle)
            except NVMLError as err:
                vbios = handleError(err)

            strResult += '    <vbios_version>' + vbios + '</vbios_version>\n'

            strResult += '    <inforom_version>\n'
            
            try:
                img = nvmlDeviceGetInforomImageVersion(handle)
            except NVMLError as err:
                img = handleError(err)
                
            strResult += '      <img_version>' + img + '</img_version>\n'

            try:
                oem = nvmlDeviceGetInforomVersion(handle, NVML_INFOROM_OEM)
            except NVMLError as err:
                oem = handleError(err)
                
            strResult += '      <oem_object>' + oem + '</oem_object>\n'
            
            try:
                ecc = nvmlDeviceGetInforomVersion(handle, NVML_INFOROM_ECC)
            except NVMLError as err:
                ecc = handleError(err)
            
            strResult += '      <ecc_object>' + ecc + '</ecc_object>\n'

            try:
                pwr = nvmlDeviceGetInforomVersion(handle, NVML_INFOROM_POWER)
            except NVMLError as err:
                pwr = handleError(err)
            
            strResult += '      <pwr_object>' + pwr + '</pwr_object>\n'
                       
            strResult += '    </inforom_version>\n'

            strResult += '    <gpu_operation_mode>\n'

            try:
                current = StrGOM(nvmlDeviceGetCurrentGpuOperationMode(handle))
            except NVMLError as err:
                current = handleError(err)
            strResult += '      <current_gom>' + current + '</current_gom>\n'

            try:
                pending = StrGOM(nvmlDeviceGetPendingGpuOperationMode(handle))
            except NVMLError as err:
                pending = handleError(err)

            strResult += '      <pending_gom>' + pending + '</pending_gom>\n'

            strResult += '    </gpu_operation_mode>\n'

            strResult += '    <pci>\n'
            strResult += '      <pci_bus>%02X</pci_bus>\n' % pciInfo.bus
            strResult += '      <pci_device>%02X</pci_device>\n' % pciInfo.device
            strResult += '      <pci_domain>%04X</pci_domain>\n' % pciInfo.domain
            strResult += '      <pci_device_id>%08X</pci_device_id>\n' % (pciInfo.pciDeviceId)
            strResult += '      <pci_bus_id>' + str(pciInfo.busId) + '</pci_bus_id>\n'
            strResult += '      <pci_sub_system_id>%08X</pci_sub_system_id>\n' % (pciInfo.pciSubSystemId)
            strResult += '      <pci_gpu_link_info>\n'


            strResult += '        <pcie_gen>\n'

            try:
                gen = str(nvmlDeviceGetMaxPcieLinkGeneration(handle))
            except NVMLError as err:
                gen = handleError(err)

            strResult += '          <max_link_gen>' + gen + '</max_link_gen>\n'

            try:
                gen = str(nvmlDeviceGetCurrPcieLinkGeneration(handle))
            except NVMLError as err:
                gen = handleError(err)

            strResult += '          <current_link_gen>' + gen + '</current_link_gen>\n'
            strResult += '        </pcie_gen>\n'
            strResult += '        <link_widths>\n'

            try:
                width = str(nvmlDeviceGetMaxPcieLinkWidth(handle)) + 'x'
            except NVMLError as err:
                width = handleError(err)

            strResult += '          <max_link_width>' + width + '</max_link_width>\n'

            try:
                width = str(nvmlDeviceGetCurrPcieLinkWidth(handle)) + 'x'
            except NVMLError as err:
                width = handleError(err)

            strResult += '          <current_link_width>' + width + '</current_link_width>\n'

            strResult += '        </link_widths>\n'
            strResult += '      </pci_gpu_link_info>\n'
            strResult += '    </pci>\n'

            try:
                fan = str(nvmlDeviceGetFanSpeed(handle)) + ' %'
            except NVMLError as err:
                fan = handleError(err)
            strResult += '    <fan_speed>' + fan + '</fan_speed>\n'

            try:
                perfState = nvmlDeviceGetPowerState(handle)
                perfStateStr = 'P%s' % perfState
            except NVMLError as err:
                perfStateStr = handleError(err)
            strResult += '    <performance_state>' + perfStateStr + '</performance_state>\n'

            strResult += GetClocksThrottleReasons(handle);

            try:
                memInfo = nvmlDeviceGetMemoryInfo(handle)
                mem_total = str(memInfo.total / 1024 / 1024) + ' MB'
                mem_used = str(memInfo.used / 1024 / 1024) + ' MB'
                mem_free = str(memInfo.total / 1024 / 1024 - memInfo.used / 1024 / 1024) + ' MB'
            except NVMLError as err:
                error = handleError(err)
                mem_total = error
                mem_used = error
                mem_free = error

            strResult += '    <memory_usage>\n'
            strResult += '      <total>' + mem_total + '</total>\n'
            strResult += '      <used>' + mem_used + '</used>\n'
            strResult += '      <free>' + mem_free + '</free>\n'
            strResult += '    </memory_usage>\n'

            
            try:
                mode = nvmlDeviceGetComputeMode(handle)
                if mode == NVML_COMPUTEMODE_DEFAULT:
                    modeStr = 'Default'
                elif mode == NVML_COMPUTEMODE_EXCLUSIVE_THREAD:
                    modeStr = 'Exclusive Thread'
                elif mode == NVML_COMPUTEMODE_PROHIBITED:
                    modeStr = 'Prohibited'
                elif mode == NVML_COMPUTEMODE_EXCLUSIVE_PROCESS:
                    modeStr = 'Exclusive Process'
                else:
                    modeStr = 'Unknown'
            except NVMLError as err:
                modeStr = handleError(err)

            strResult += '    <compute_mode>' + modeStr + '</compute_mode>\n'

            try:
                util = nvmlDeviceGetUtilizationRates(handle)
                gpu_util = str(util.gpu) + ' %'
                mem_util = str(util.memory) + ' %'
            except NVMLError as err:
                error = handleError(err)
                gpu_util = error
                mem_util = error
            
            strResult += '    <utilization>\n'
            strResult += '      <gpu_util>' + gpu_util + '</gpu_util>\n'
            strResult += '      <memory_util>' + mem_util + '</memory_util>\n'
            strResult += '    </utilization>\n'
            
            try:
                (current, pending) = nvmlDeviceGetEccMode(handle)
                curr_str = 'Enabled' if (current != 0) else 'Disabled'
                pend_str = 'Enabled' if (pending != 0) else 'Disabled'
            except NVMLError as err:
                error = handleError(err)
                curr_str = error
                pend_str = error

            strResult += '    <ecc_mode>\n'
            strResult += '      <current_ecc>' + curr_str + '</current_ecc>\n'
            strResult += '      <pending_ecc>' + pend_str + '</pending_ecc>\n'
            strResult += '    </ecc_mode>\n'

            strResult += '    <ecc_errors>\n'
            strResult += GetEccStr(handle)
            strResult += '    </ecc_errors>\n'
            
            try:
                temp = str(nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)) + ' C'
            except NVMLError as err:
                temp = handleError(err)

            strResult += '    <temperature>\n'
            strResult += '      <gpu_temp>' + temp + '</gpu_temp>\n'
            strResult += '    </temperature>\n'

            strResult += '    <power_readings>\n'
            try:
                perfState = 'P' + str(nvmlDeviceGetPowerState(handle))
            except NVMLError as err:
                perfState = handleError(err)
            strResult += '      <power_state>%s</power_state>\n' % perfState
            try:
                powMan = nvmlDeviceGetPowerManagementMode(handle)
                powManStr = 'Supported' if powMan != 0 else 'N/A'
            except NVMLError as err:
                powManStr = handleError(err)
            strResult += '      <power_management>' + powManStr + '</power_management>\n'
            try:
                powDraw = (nvmlDeviceGetPowerUsage(handle) / 1000.0)
                powDrawStr = '%.2f W' % powDraw
            except NVMLError as err:
                powDrawStr = handleError(err)
            strResult += '      <power_draw>' + powDrawStr + '</power_draw>\n'
            try:
                powLimit = (nvmlDeviceGetPowerManagementLimit(handle) / 1000.0)
                powLimitStr = '%.2f W' % powLimit
            except NVMLError as err:
                powLimitStr = handleError(err)
            strResult += '      <power_limit>' + powLimitStr + '</power_limit>\n'
            try:
                powLimit = (nvmlDeviceGetPowerManagementDefaultLimit(handle) / 1000.0)
                powLimitStr = '%.2f W' % powLimit
            except NVMLError as err:
                powLimitStr = handleError(err)
            strResult += '      <default_power_limit>' + powLimitStr + '</default_power_limit>\n'
            try:
                powLimit = nvmlDeviceGetPowerManagementLimitConstraints(handle)
                powLimitStrMin = '%.2f W' % (powLimit[0] / 1000.0)
                powLimitStrMax = '%.2f W' % (powLimit[1] / 1000.0)
            except NVMLError as err:
                error = handleError(err)
                powLimitStrMin = error
                powLimitStrMax = error
            strResult += '      <min_power_limit>' + powLimitStrMin + '</min_power_limit>\n'
            strResult += '      <max_power_limit>' + powLimitStrMax + '</max_power_limit>\n'

            strResult += '    </power_readings>\n'

            strResult += '    <clocks>\n'
            try:
                graphics = str(nvmlDeviceGetClockInfo(handle, NVML_CLOCK_GRAPHICS))
            except NVMLError as err:
                graphics = handleError(err)
            strResult += '      <graphics_clock>' +graphics + ' MHz</graphics_clock>\n'
            try:
                sm = str(nvmlDeviceGetClockInfo(handle, NVML_CLOCK_SM)) + ' MHz'
            except NVMLError as err:
                sm = handleError(err)
            strResult += '      <sm_clock>' + sm + '</sm_clock>\n'
            try:
                mem = str(nvmlDeviceGetClockInfo(handle, NVML_CLOCK_MEM)) + ' MHz'
            except NVMLError as err:
                mem = handleError(err)
            strResult += '      <mem_clock>' + mem + '</mem_clock>\n'
            strResult += '    </clocks>\n'

            strResult += '    <applications_clocks>\n'
            try:
                graphics = str(nvmlDeviceGetApplicationsClock(handle, NVML_CLOCK_GRAPHICS)) + ' MHz'
            except NVMLError as err:
                graphics = handleError(err)
            strResult += '      <graphics_clock>' +graphics + '</graphics_clock>\n'
            try:
                mem = str(nvmlDeviceGetApplicationsClock(handle, NVML_CLOCK_MEM)) + ' MHz'
            except NVMLError as err:
                mem = handleError(err)
            strResult += '      <mem_clock>' + mem + '</mem_clock>\n'
            strResult += '    </applications_clocks>\n'

            strResult += '    <max_clocks>\n'
            try:
                graphics = str(nvmlDeviceGetMaxClockInfo(handle, NVML_CLOCK_GRAPHICS)) + ' MHz'
            except NVMLError as err:
                graphics = handleError(err)
            strResult += '      <graphics_clock>' + graphics + '</graphics_clock>\n'
            try:
                sm = str(nvmlDeviceGetMaxClockInfo(handle, NVML_CLOCK_SM)) + ' MHz'
            except NVMLError as err:
                sm = handleError(err)
            strResult += '      <sm_clock>' + sm + '</sm_clock>\n'
            try:
                mem = str(nvmlDeviceGetMaxClockInfo(handle, NVML_CLOCK_MEM)) + ' MHz'
            except NVMLError as err:
                mem = handleError(err)
            strResult += '      <mem_clock>' + mem + '</mem_clock>\n'
            strResult += '    </max_clocks>\n'

            try:
                memClocks = nvmlDeviceGetSupportedMemoryClocks(handle)
                strResult += '    <supported_clocks>\n'

                for m in memClocks:
                    strResult += '      <supported_mem_clock>\n'
                    strResult += '        <value>%d MHz</value>\n' % m
                    try:
                        clocks = nvmlDeviceGetSupportedGraphicsClocks(handle, m)
                        for c in clocks:
                            strResult += '        <supported_graphics_clock>%d MHz</supported_graphics_clock>\n' % c
                    except NVMLError as err:
                        strResult += '        <supported_graphics_clock>%s</supported_graphics_clock>\n' % handleError(err)
                    strResult += '      </supported_mem_clock>\n'

                strResult += '    </supported_clocks>\n'
            except NVMLError as err:
                strResult += '    <supported_clocks>' + handleError(err) + '</supported_clocks>\n'

            try:
                procs = nvmlDeviceGetComputeRunningProcesses(handle)
                strResult += '    <compute_processes>\n'
             
                for p in procs:
                    try:
                        name = str(nvmlSystemGetProcessName(p.pid))
                    except NVMLError as err:
                        if (err.value == NVML_ERROR_NOT_FOUND):
                            # probably went away
                            continue
                        else:
                            name = handleError(err)
                    
                    strResult += '    <process_info>\n'
                    strResult += '      <pid>%d</pid>\n' % p.pid
                    strResult += '      <process_name>' + name + '</process_name>\n'

                    if (p.usedGpuMemory == None):
                        mem = 'N\A'
                    else:
                        mem = '%d MB' % (p.usedGpuMemory / 1024 / 1024)
                    strResult += '      <used_memory>' + mem + '</used_memory>\n'
                    strResult += '    </process_info>\n'
                
                strResult += '    </compute_processes>\n'
            except NVMLError as err:
                strResult += '    <compute_processes>' + handleError(err) + '</compute_processes>\n'

            strResult += '  </gpu>\n'
            
        strResult += '</nvidia_smi_log>\n'
        
    except NVMLError as err:
        strResult += 'nvidia_smi.py: ' + err.__str__() + '\n'
    
    nvmlShutdown()
    
    return strResult

