package com.oblixorprime.immersivebopharvest.qa;

import com.google.gson.GsonBuilder;
import net.minecraft.gametest.framework.GameTestInfo;
import net.minecraft.gametest.framework.GlobalTestReporter;
import net.minecraft.gametest.framework.LogTestReporter;
import net.minecraft.gametest.framework.TestReporter;
import net.neoforged.fml.ModList;
import net.neoforged.fml.common.Mod;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Mod("bop_harvest_qa")
public final class QualificationMod {
    public QualificationMod() {
        PackagedRuntime.install();
        if (Boolean.getBoolean("neoforge.gameTestServer")) {
            GlobalTestReporter.replaceWith(new Reporter());
        }
    }

    private static final class Reporter implements TestReporter {
        private final LogTestReporter delegate = new LogTestReporter();
        private final List<Map<String, Object>> cases = new ArrayList<>();
        @Override public void onTestFailed(GameTestInfo info) {
            delegate.onTestFailed(info);
            record(info, false);
        }
        @Override public void onTestSuccess(GameTestInfo info) {
            delegate.onTestSuccess(info);
            record(info, true);
        }
        private void record(GameTestInfo info, boolean pass) {
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("id", info.getTestName());
            row.put("passed", pass);
            row.put("required", info.isRequired());
            row.put("runTimeMs", info.getRunTime());
            row.put("error", pass ? null : String.valueOf(info.getError()));
            cases.add(row);
        }
        @Override public void finish() {
            try {
                Map<String, Object> report = new LinkedHashMap<>();
                report.put("schemaVersion", 1);
                report.put("executionMode", "development-classpath");
                report.put("candidateVersion", ModList.get().getModContainerById("immersive_bop_harvest").orElseThrow().getModInfo().getVersion().toString());
                report.put("cases", cases);
                report.put("assertions", QualificationChecks.observations());
                Path target = Path.of(System.getProperty("bop.qa.report"));
                Files.createDirectories(target.toAbsolutePath().getParent());
                Files.writeString(target, new GsonBuilder().setPrettyPrinting().create().toJson(report) + "\n");
            } catch (Exception e) {
                throw new IllegalStateException("Cannot retain actual qualification results", e);
            }
        }
    }
}
